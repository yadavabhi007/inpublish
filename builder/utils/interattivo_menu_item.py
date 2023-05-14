from django.urls import resolve
from menu import MenuItem


class InterattivoMenuItem(MenuItem):
    def __init__(self, title, url, **kwargs):
        self.function = ""
        self.id_perms = ""
        self.user = None
        self.is_free = True
        self.is_essential = False
        super().__init__(title, url, **kwargs)

    def on_click(self):
        if self.id_perms == "perm-interactive_index":
            if self.user.interactive_index:
                return self.function
            else:
                return ""

        if self.user.permission_pack > 3:  # da standard in su
            return self.function
        elif self.user.is_free_user() and not self.is_free:
            return ""
        elif self.user.is_essential_user() and not self.is_essential:
            return ""
        else:
            return self.function

    def css_class(self):
        if self.id_perms == "perm-interactive_index":
            if self.user.interactive_index:
                return ""
            else:
                return "no-permission"

        if self.user.permission_pack > 3:  # da standard in su
            return ""
        elif self.user.is_free_user() and not self.is_free:
            return "no-permission"
        elif self.user.is_essential_user() and not self.is_essential:
            return "no-permission"
        else:
            return ""

    def check(self, request):
        self.user = request.user
        self.visible = (
            resolve(request.path_info).url_name == "edit_interactive_flyer"
        )
