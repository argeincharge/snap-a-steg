# Snap-A-Steg: secure image steganography app
# Copyright (C) 2025 argeincharge
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.


from kivy.utils import get_color_from_hex

def toggle_password_visibility(password_input, toggle_button):
    password_input.password = not password_input.password
    toggle_button.text = "View" if password_input.password else "Hide"


def update_checklist_and_button(
    password_input, secret_input, checklist_labels, requirements,
    bytes_info_label, encode_button, edited_image, calculate_max_message_size_func
):
    pwd = password_input.text
    secret = secret_input.text
    all_met = True

    for req, check in requirements.items():
        met = bool(check(pwd))
        label = checklist_labels[req]
        if met:
            label.text = f"✅ {req}"
            label.color = get_color_from_hex("#00FF00")  # green
        else:
            label.text = f"❌ {req}"
            label.color = get_color_from_hex("#FF0000")  # red
            all_met = False

    if edited_image:
        try:
            max_bytes = calculate_max_message_size_func(edited_image)
            msg_bytes = len(secret.encode("utf-8"))
            bytes_info_label.text = f"{msg_bytes} / {max_bytes} bytes used"
            can_encode = all_met and secret and (msg_bytes <= max_bytes)
        except Exception:
            bytes_info_label.text = "Error calculating capacity"
            can_encode = False
    else:
        bytes_info_label.text = "0 / ? bytes used"
        can_encode = False

    encode_button.disabled = not can_encode
