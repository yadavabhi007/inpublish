import requests

from builder.utils.base_class.check_string_class import CounterCheck


class PermissionsUtils(CounterCheck):
    def search_perm_by_id(self, permission_id, default_value=False):
        for perm in self.response["data"]["caratteristiche"]:
            if perm["id"] == permission_id:
                if perm["valore"] == 0:
                    return perm["incluso"] == 1
                else:
                    return perm["valore"]

        return default_value

    def get_permissions(self, user):
        check_string = self.calculate_counter_check()

        url = (
            f"https://portale.volantinointerattivo.net/api/gestionale/get-capabilities"
            f"?token={user.token}&check_string={check_string}&id_servizio=1"
        )
        # log_debug("tokens:", f"{user.token} {check_string} {url}")
        self.response = requests.get(url).json()

        if self.response["status"] == 200 and self.response["error_code"] == 0:
            return self.response["data"]
        else:
            return None
