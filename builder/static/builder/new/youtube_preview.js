/* jshint esversion: 6 */

$(document).ready(function () {
    let linkInputText = $('.youtube-link-field');
    $.each(linkInputText, (_, item) => {
        const target = item.getAttribute('data-target');

        $(item).on('change', (e) => {
            const value = $(item).val();
            let videoId = '';
            try {
                let myRegexp = new RegExp("^.*(youtu.be\\/|v\\/|embed\\/|watch\\?|youtube.com\\/user\\/[^#]*#([^\\/]*?\\/)*)\\??v?=?([^#\\&\\?]*).*", "g");
                let match = myRegexp.exec(value);
                videoId = match[3];
            } catch (e) {
                $(item).val('');
                Swal.fire({
                    icon: 'error',
                    title: `${gettext('Oops...')}`,
                    text: `${gettext('Il link che hai inserito non è valido')}`,
                });
                return;
            }

            $(target).removeClass('d-none');
            $(`${target} iframe`).attr('src', "https://www.youtube.com/embed/" + videoId);
            $(item).val("https://www.youtube.com/watch/" + videoId);
        });
    });
});
