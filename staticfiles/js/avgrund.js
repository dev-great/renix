(function ($) {
  "use strict";
  $(function () {
    $("#show").avgrund({
      height: 250,
      holderClass: "custom",
      showClose: true,
      showCloseText: "x",
      onBlurContainer: ".container-scroller",
      template:
        "<p>Select your subscription duration timeline and make payment to gain full access to the system.</p>" +
        "<div>" +
        '<a href="http://twitter.com/voronianski" target="_blank" class="btn btn-outline-primary btn-block">Monthly Payment</a>' +
        '<a href="http://dribbble.com/voronianski" target="_blank" class="btn btn-success btn-block">Yearly Payment</a>' +
        "</div>",
    });
  });
})(jQuery);
