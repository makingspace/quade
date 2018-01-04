from __future__ import absolute_import, division, print_function, unicode_literals

from django import forms
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
try:
    from django.urls import reverse, reverse_lazy
except ImportError:
    from django.core.urlresolvers import reverse, reverse_lazy
from django.views.generic import View, FormView

from .compatability import UserPassesTestMixin
from .models import QATestRecord, QATestScenario
from .tasks import execute_test_task


class SuperUserAccessMixin(UserPassesTestMixin):

    test_func = lambda x: x.request.user.is_superuser
    raise_exception = True


class ExecuteTestForm(forms.Form):
    scenarios = forms.ModelChoiceField(
        queryset=QATestScenario.objects.none(),
        to_field_name='slug'
    )

    def __init__(self, *args, **kwargs):
        # Overwrite the queryset when the form is initialized to avoid stale data.
        super(ExecuteTestForm, self).__init__(*args, **kwargs)
        self.fields['scenarios'].queryset = QATestScenario.objects.active()

    def execute_test(self, created_by):
        scenario = self.cleaned_data['scenarios']
        record = QATestRecord.objects.create(scenario=scenario, created_by=created_by)
        execute_test_task.delay(record.id)
        return record


class MainView(SuperUserAccessMixin, FormView):
    template_name = 'quade/main.jinja'
    form_class = ExecuteTestForm
    success_url = reverse_lazy('qa-main')

    def get_context_data(self, **kwargs):
        context = super(MainView, self).get_context_data(**kwargs)
        # Remove the form from the context if there are no active tests currently.
        # (The default "-------" will always be present.)
        if self.request.method == 'GET' and len(context['form'].fields['scenarios'].choices) <= 1:
            context['form'] = None
        context['allowed'] = settings.QUADE.allowed
        context['recent_tests'] = QATestRecord.objects.all().order_by(
            '-created_on'
        ).select_related('scenario')[:30]
        return context

    def form_valid(self, form):
        form.execute_test(created_by=self.request.user)
        return super(MainView, self).form_valid(form)


class MarkDoneView(SuperUserAccessMixin, View):
    def post(self, request, test_record_id):
        record = get_object_or_404(QATestRecord, id=test_record_id)
        record.status = QATestRecord.Status.DONE
        record.save()
        return HttpResponseRedirect(reverse('qa-main'))
