from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect
from django.views.generic.base import ContextMixin, View, TemplateResponseMixin
from django.urls import reverse
from django.http import JsonResponse
from collections import namedtuple


MyCustomForm = namedtuple('MyCustomForm', 'name trigger add_request to_save', defaults=(False, False))


class MultipleFormViewMixin(ContextMixin):
    form_classes = []
    success_urls = {}

    def get_form_classes(self):
        return self.form_classes

    def get_forms(self, form_classes=[]):
        if form_classes == []:
            form_classes = self.get_form_classes()
        return {form_class.name.__name__: form_class.name(**self.get_form_kwargs(form_class)) for form_class in form_classes}

    def get_form_kwargs(self, form=None):
        kwargs = {}
        if form and form.add_request:
            print('[REQUEST ADDED]')
            kwargs.update({
                        'request': self.request, 
            })
        if self.request.method in ('POST', 'PUT'):
            if form and getattr(self.request, self.request.method).get(form.trigger, None) is not None:
                print('[TRIGGER DETECTES]')
                kwargs.update({
                    'data': self.request.POST,
                    'files': self.request.FILES,
                })
        return kwargs

    def get_success_url(self, form, kw={}):
        url = self.success_urls.get(form.name, None)
        print('[URL] ',url)
        if url is None:
            raise ImproperlyConfigured("No URL to redirect to. Provide a success_url.")
        return reverse(url, kwargs=kw)  # success_url may be lazy

    def form_valid(self, form, kw={}):
        print(f'[FORM]: {form},[KWARGS] {kw}')
        if form.to_save:
            form.name.save()
        return HttpResponseRedirect(self.get_success_url(form, kw))

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        for (name, form) in self.get_forms().items():
            key = 'form_'+ name
            if key not in kwargs:
                kwargs[key] = form
        print('[KWARGS FOR FORM] ', kwargs)
        return super().get_context_data(**kwargs)


class ProcessMultipleFormView(View):
    def get(self, request, *args, **kwargs):
        print('[GET]')
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        if self.is_ajax(request):
            print('[AJAX]')
            response = self.do_ajax_stuff(request, 'POST')
            return JsonResponse(response)
        else:
            print('[NOT AJAX]')
            form_classes = self.get_form_classes()
            for form in form_classes:
                if form.trigger:
                    print('[FORM] ', form, form.name)
                    form_wkw = [value for (_, value) in self.get_forms().items() if value.__class__ is form.name][0]
                    print(type(form_wkw), form_wkw.is_valid())
                    print(form_wkw.fields)
                    if form_wkw.is_valid():
                        print('[FORM INTERNALLY VALID]')
                        kw = self.perform_additional_action(request, form.name)
                        print('[GOT KWARGS] ', kw)
                        return self.form_valid(form, kw)
                    # else:
                    #     return self.form_invalid(form)

    def do_ajax_stuff(self, request, method, triggers=[]):
        queries = zip([getattr(request, method).get(trigger) for trigger in triggers], triggers)
        for query, trigger in queries:
            if query:
                response = getattr(self, 'query_'+trigger)(query)
                return response


    def is_ajax(self, request):
        return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
                   
    def perform_additional_action(self, request, form):
        return {}


class MultipleFormView(MultipleFormViewMixin, TemplateResponseMixin, ProcessMultipleFormView):
    """A view for displaying multiple forms at the same time and rendering a template response."""