/* jshint esversion: 6 */

$(document).ready(function () {
    let fileInputs = $('.live_preview');
    $.each(fileInputs, (_, item) => {
        const target = item.getAttribute('data-target');

        $(item).on('change', (e) => {
            const [file] = item.files;
            if (file) {
                $(target).attr("src", URL.createObjectURL(file));
            }
        });
    });
});
