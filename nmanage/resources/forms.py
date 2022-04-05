from django import forms

class ScheduleForm(forms.Form):
  disabled = forms.BooleanField(initial=False, required=False)

  monday_on = forms.TimeField(required=False)
  monday_off = forms.TimeField(required=False)

  tuesday_on = forms.TimeField(required=False)
  tuesday_off = forms.TimeField(required=False)

  wednesday_on = forms.TimeField(required=False)
  wednesday_off = forms.TimeField(required=False)

  thursday_on = forms.TimeField(required=False)
  thursday_off = forms.TimeField(required=False)

  friday_on = forms.TimeField(required=False)
  friday_off = forms.TimeField(required=False)

  saturday_on = forms.TimeField(required=False)
  saturday_off = forms.TimeField(required=False)

  sunday_on = forms.TimeField(required=False)
  sunday_off = forms.TimeField(required=False)
