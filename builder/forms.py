from django import forms

from builder.models import ClientSetting


class ClientSettingForm(forms.ModelForm):
    class Meta:
        model = ClientSetting
        fields = "__all__"
        exclude = [
            "user_client",
            "signboard_id",
            "release_id",
            "client_id",
        ]

    def __init__(self, *args, **kwargs):
        super(ClientSettingForm, self).__init__(*args, **kwargs)
        self.fields["primary_color"].widget.attrs.update(
            {
                "class": "textinput textInput form-control color-picker badil-rounded badil-color-gray "
                "badil-shadow colorpicker-element"
            }
        )
        self.fields["primary_color"].widget.attrs.update({"type": "text"})
        self.fields["secondary_color"].widget.attrs.update(
            {
                "class": "textinput textInput form-control color-picker badil-rounded badil-color-gray "
                "badil-shadow colorpicker-element"
            }
        )
        self.fields["secondary_color"].widget.attrs.update({"type": "text"})
        self.fields["tertiary_color"].widget.attrs.update(
            {
                "class": "textinput textInput form-control color-picker badil-rounded badil-color-gray "
                "badil-shadow colorpicker-element"
            }
        )
        self.fields["tertiary_color"].widget.attrs.update({"type": "text"})
        self.fields["hover_color"].widget.attrs.update(
            {
                "class": "textinput textInput form-control color-picker badil-rounded badil-color-gray "
                "badil-shadow colorpicker-element"
            }
        )
        self.fields["hover_color"].widget.attrs.update({"type": "text"})
