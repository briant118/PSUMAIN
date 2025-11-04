$(document).ready(function () {
  console.log("Registration.js loaded");
  
  // Email validation regex
  var regex = /^[a-zA-Z0-9]+$/;
  
  // Registration script
  // Handle next button clicks
  $(".next").click(function(){
    console.log("Next button clicked");
    var nextStep = $(this).data("next");
    console.log("Next step:", nextStep);

    // if role button clicked, set role value
    if($(this).data("role")){
      var role = $(this).data("role");
      console.log("Role selected:", role);
      $("#role").val(role);
    }

    $(this).closest(".step").removeClass("active");
    $("#" + nextStep).addClass("active");
    console.log("Step changed to:", nextStep);
  });

  // Handle form submit
  $("#registrationForm").on("submit", function(e) {
    // Validate email prefix
    var prefix = $("#email_prefix").val().trim();
    var domain = "@psu.palawan.edu.ph";

    if (!regex.test(prefix)) {
      alert("Email prefix must only contain letters and numbers (no @ or .).");
      e.preventDefault();
      return false;
    }

    // Validate password match
    var password = $('input[name="password"]').val();
    var password2 = $('input[name="password2"]').val();
    
    if (password !== password2) {
      alert("Passwords do not match. Please re-enter your password.");
      e.preventDefault();
      return false;
    }
  });

  $("#code4").on("input", function() {
    var codes = [];
    var code_str = ""
    for (var i = 1; i < 5; i++){
      code_str = "#code"+i
      codes.push($(code_str).val());
    }
    $("#code").val(codes.join(''));
    // console.log("codes", codes.join(''));
  });
  
  $("#code1").on("input", function() {
    $("#code2").focus();
  });
  
  $("#code2").on("input", function() {
    $("#code3").focus();
  });
  
  $("#code3").on("input", function() {
    $("#code4").focus();
  });

});
