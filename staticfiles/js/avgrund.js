function payWithPaystack() {
  var handler = PaystackPop.setup({
    key: "pk_test_91130c972c5af7ec4b37e1a4a9428eb128d41f68",
    email: "gmarshal070@gmail.com",
    amount: 100000,
    currency: "NGN",
    ref: "" + Math.floor(Math.random() * 1000000000 + 1),
    metadata: {
      custom_fields: [
        {
          display_name: "Greatness Marshal",
          variable_name: "08100808038",
          value: "+2348012345678",
        },
      ],
    },
    callback: function (response) {
      alert("success. transaction ref is " + response.reference);
    },
    onClose: function () {
      alert("window closed");
    },
  });
  handler.openIframe();
}

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
        '<a href="#" onclick="payWithPaystack(); return false;" class="btn btn-outline-primary btn-block">Monthly Payment</a>' +
        '<a href="#" onclick="payWithPaystack(); return false;" class="btn btn-success btn-block">Yearly Payment</a>' +
        "</div>",
    });
  });
})(jQuery);
