from django import forms


class ParticipantForm(forms.Form):

    name = forms.CharField(
        max_length=100,
        label="Full Name",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your full name"
        })
    )

    age = forms.IntegerField(
        min_value=18,
        max_value=100,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "Enter your age"
        })
    )

    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]

    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        widget=forms.RadioSelect(attrs={
            "class": "form-check-input"
        })
    )


class LifestyleForm(forms.Form):

    sleep_duration = forms.FloatField(
        label="Sleep Duration",
        min_value=3,
        max_value=12,
        widget=forms.NumberInput(attrs={
            "type": "range",
            "class": "form-range",
            "min": "3",
            "max": "12",
            "step": "0.5",
            "value": "7",
            "id": "id_sleep_duration"
        })
    )

    stress_level = forms.IntegerField(
        label="Stress Level",
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={
            "type": "range",
            "class": "form-range",
            "min": "1",
            "max": "10",
            "step": "1",
            "value": "5",
            "id": "id_stress_level"
        })
    )

    SCREEN_TIME_CHOICES = [
        ("<2", "Less than 2 Hours"),
        ("2-4", "2 - 4 Hours"),
        ("4-6", "4 - 6 Hours"),
        ("6-8", "6 - 8 Hours"),
        ("8+", "More than 8 Hours"),
    ]

    screen_time = forms.ChoiceField(
        label="Daily Screen Time",
        choices=SCREEN_TIME_CHOICES,
        widget=forms.RadioSelect
    )

    EXERCISE_CHOICES = [
        ("Never", "Never"),
        ("1-2", "1–2 Days / Week"),
        ("3-5", "3–5 Days / Week"),
        ("Daily", "Daily"),
    ]

    exercise_frequency = forms.ChoiceField(
        label="Exercise Frequency",
        choices=EXERCISE_CHOICES,
        widget=forms.RadioSelect
    )