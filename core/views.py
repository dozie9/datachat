from django.http import HttpResponseNotAllowed
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, FormView

from core.forms import DataUploadForm, QueryForm
from core.models import Conversation, Message
from utils import langchain_helper


class Home(TemplateView):
    template_name = 'core/base.html'


class DataUploadView(FormView):
    http_method_names = ['post']
    form_class = DataUploadForm
    template_name = 'core/base.html'

    def get_success_url(self):
        print('get_success_url')
        return '/'

    def form_valid(self, form):
        print('form_valid')
        attachment = form.cleaned_data['attachment']
        query = 'Analyze the data and come up with a meaningful insight. Consider all available columns. Illustrate this insight with a graph using matplotlib'

        response = langchain_helper.file_query(attachment, query)
        # print(response)
        conversation = Conversation.objects.create(
            attachment=attachment,
            title='Test title',
            user1=self.request.user
        )
        Message.objects.create(
            user=self.request.user,
            conversation=conversation,
            content=response
        )
        self.request.session['conversation_id'] = str(conversation.id)

        return super().form_valid(form)


class FileChatView(FormView):
    # http_method_names = ['post']
    form_class = QueryForm
    template_name = 'core/base.html'

    def get_success_url(self):
        return self.request.path

    def form_valid(self, form):
        query = form.cleaned_data['query']
        # print(query)
        # conversation_id = self.request.session.get('conversation_id')
        conversation_id = self.kwargs.get('conversation_id')
        conversation = Conversation.objects.get(id=conversation_id)

        response = langchain_helper.file_query(conversation.attachment.path, query)

        Message.objects.create(
            user=self.request.user,
            conversation=conversation,
            content=query
        )
        Message.objects.create(
            # user=self.request.user,
            conversation=conversation,
            content=response
        )
        # self.request.session['conversation_id'] = conversation.id

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        conversation = Conversation.objects.get(id=self.kwargs.get('conversation_id'))
        ctx.update({
            'conversation': conversation,
            'messages': conversation.message_set.all()
        })
        return ctx
