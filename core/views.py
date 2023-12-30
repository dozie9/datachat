from django.http import HttpResponseNotAllowed
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, FormView

from core.forms import DataUploadForm
from utils import langchain_helper


class Home(TemplateView):
    template_name = 'core/base2.html'


class DataUploadView(FormView):
    http_method_names = ['post']
    form_class = DataUploadForm
    template_name = 'core/base2.html'

    def get_success_url(self):
        return '/'

    def get(self, request, *args, **kwargs):
        # Option 1: Return an HTTP 405 Method Not Allowed response
        # return HttpResponseNotAllowed(['POST'])
        return redirect('/')

    def form_valid(self, form):
        attachment = form.cleaned_data['attachment']
        query = 'tell me something about the data. illustrate with graph'

        response = langchain_helper.file_query(attachment, query)
        print(response)

        return super().form_valid(form)
