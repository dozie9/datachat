from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseNotAllowed
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import TemplateView, FormView, ListView

from core.forms import DataUploadForm, QueryForm, DBForm
from core.models import Conversation, Message
from utils import langchain_helper


class Home(LoginRequiredMixin, TemplateView):
    template_name = 'core/home.html'


class DataUploadView(FormView):
    http_method_names = ['post']
    form_class = DataUploadForm
    template_name = 'core/chat.html'

    # def get_success_url(self):
    #     print('get_success_url')
    #     return '/'

    def form_valid(self, form):
        print('form_valid')
        attachment = form.cleaned_data['attachment']
        query = 'Analyze the data and come up with a meaningful insight. Consider all columns.' # Illustrate this insight with a graph using matplotlib'
        try:
            # print(response)
            conversation = Conversation.objects.create(
                attachment=attachment,
                title='Test title',
                user1=self.request.user
            )
            user_msg = Message.objects.create(
                user=self.request.user,
                conversation=conversation,
                content=conversation.attachment.name.split('/',)[-1]
            )

            ai_msg = Message.objects.create(
                # user=self.request.user,
                conversation=conversation,
                # content=conversation.attachment.name
            )
            response = langchain_helper.file_query(conversation.attachment.path, query, ai_msg)
            ai_msg.content = response
            ai_msg.save()
        except (ValueError,) as e:
            messages.warning(self.request, "Something went wrong please try again.")
            return redirect('/')
        # self.request.session['conversation_id'] = str(conversation.id)

        return redirect(reverse('core:file-chat', args=[conversation.id]))


class FileChatView(FormView):
    # http_method_names = ['post']
    form_class = QueryForm
    template_name = 'core/chat.html'

    def get_success_url(self):
        conversation_id = self.kwargs.get('conversation_id')
        return reverse('core:messages', args=[conversation_id])

    def form_valid(self, form):
        query = form.cleaned_data['query']
        # print(query)
        # conversation_id = self.request.session.get('conversation_id')
        conversation_id = self.kwargs.get('conversation_id')
        conversation = Conversation.objects.get(id=conversation_id)
        Message.objects.create(
            user=self.request.user,
            conversation=conversation,
            content=query
        )

        ai_msg = Message.objects.create(
            # user=self.request.user,
            conversation=conversation,
            # content=response
        )
        if conversation.data_type == Conversation.DB:
            response = langchain_helper.sql_query(query, conversation.connection_string, ai_msg)
        else:
            response = langchain_helper.file_query(ai_msg.conversation.attachment.path, query, ai_msg)
        ai_msg.content = response
        ai_msg.save()

        # self.request.session['conversation_id'] = conversation.id

        return redirect(reverse('core:messages', args=[conversation.id]))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        conversation = Conversation.objects.get(id=self.kwargs.get('conversation_id'))
        ctx.update({
            'conversation': conversation,
            'message_list': conversation.message_set.all()
        })
        return ctx


class CreateDBConvoView(FormView):
    form_class = DBForm
    template_name = 'core/chat.html'
    http_method_names = ['post']

    def form_valid(self, form):
        table_name = form.cleaned_data['connection_string']
        # query = 'Analyze the data and come up with a meaningful insight. Consider all columns.' # Illustrate this insight with a graph using matplotlib'
        query = f'Tell me something about {table_name}'
        # print(response)
        conversation = Conversation.objects.create(
            title='Test title',
            user1=self.request.user,
            connection_string=table_name,
            data_type=Conversation.DB
        )
        user_msg = Message.objects.create(
            user=self.request.user,
            conversation=conversation,
            content=table_name
        )

        ai_msg = Message.objects.create(
            # user=self.request.user,
            conversation=conversation,
            # content=conversation.attachment.name
        )
        response = langchain_helper.sql_query(query, table_name, ai_msg)
        ai_msg.content = response
        ai_msg.save()
        # self.request.session['conversation_id'] = str(conversation.id)

        return redirect(reverse('core:file-chat', args=[conversation.id]))


class MessageListView(ListView):
    template_name = 'core/messages.html'

    def get_queryset(self):
        conversation_id = self.kwargs.get('conversation_id')
        return Message.objects.filter(conversation__id=conversation_id)
