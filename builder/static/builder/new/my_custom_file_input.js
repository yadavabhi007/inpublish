/* jshint esversion: 6 */

$(document).ready(function () {
    let fileInputs = $('.my-custom-file-input');
    $.each(fileInputs, (_, item) => {
        const target = item.getAttribute('data-target');
        const type = item.getAttribute('data-type');

        $(item).on('change', (e) => {
            const [file] = item.files;
            $(`label[for=${item.id}]`).html(file.name);
            if (file) {
                if (type === 'video') {
                    let video = document.createElement('video');
                    video.src = URL.createObjectURL(file);
                    video.autoplay = false;
                    video.controls = true;
                    video.className = "w-100 p-2";
                    $(target).html(video);
                } else if (type === 'img') {
                    let img = document.createElement('img');
                    img.src = URL.createObjectURL(file);
                    img.className = "p-2 max-height-preview";
                    $(target).html(img);
                }
            }
        });
    });
});
