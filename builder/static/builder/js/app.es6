App = {
  show_loader: function (el = false) {
    if (el) {
      $(el).LoadingOverlay("show", {
        imageColor: "#343a40"
      });
    } else {
      $.LoadingOverlay("show", {
        imageColor: "#343a40"
      });
    }
  },

  hide_loader: function (el = false) {
    if (el) {
      $(el).LoadingOverlay("hide");
    } else {
      $.LoadingOverlay("hide");
    }
  },

  show_toast: function (message) {
    $(".toast-body").html(message);
    $(".toast").toast("show");
  },

  show_feedback: function (type, message) {
    // type: alert, success, error, warning, info
    new Noty({
      theme: 'bootstrap-v4',
      type: type,
      layout: 'topCenter',
      timeout: 5000,
      text: message,
      closeWith: ["button"]
    }).show();
  },

  clone_flyer: function (source_flyer_id) {
    $("#clone-interactive-flyer-form_source_flyer_id").val(source_flyer_id);
    $("#clone-interactive-flyer-modal").modal("show");
  }

};

App.interactive_flyer = {};