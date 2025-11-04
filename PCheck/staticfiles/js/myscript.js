$(document).ready(function () {
  const $ip_address = $("#id_ip_address");
  const $connectButton = $("#connectButton");
  const $statusIndicator = $("#status_indicator");
  const $addPCbutton = $("#addPCbutton");
  const $PCformDiv = $("#PCformDiv");
  const $status = $("#id_status");
  const $name = $("#id_name");
  const $nameError = $("#name-error");
  const $ip_addressError = $("#ip-address-error");
  const $cancelButton = $("#cancel-button");
  const $repairButton = $("#repair-button");

  // Validate PC name duplication
  $name.on("change", function () {
    $.getJSON(`/ajax/verify-pc-name/?name=${$name.val()}`)
      .done(function (data) {
        if (data.error) {
          console.log(data.error);
        } else {
          if (data.result) {
            $nameError.text("PC with this name already exists.");
          } else {
            $nameError.text("");
          }
        }
      })
      .fail(function (jqXHR, textStatus, errorThrown) {
        console.error("Error fetching name data:", errorThrown);
      });
  });

  // Validate IP address duplication
  $ip_address.on("change", function () {
    $.getJSON(`/ajax/verify-pc-ip-address/?ip_address=${$ip_address.val()}`)
      .done(function (data) {
        if (data.error) {
          console.log(data.error);
        } else {
          if (data.result) {
            $ip_addressError.text("PC with this IP address already exists.");
          } else {
            $ip_addressError.text("");
          }
        }
      })
      .fail(function (jqXHR, textStatus, errorThrown) {
        console.error("Error fetching name data:", errorThrown);
      });
  });

  // Trigger ping IP address
  $connectButton.on("click", function (e) {
    e.preventDefault();
    const ipAddress = $ip_address.val();

    // Spinner
    if (
      $.trim($statusIndicator.text()) != "reachable" ||
      $.trim($statusIndicator.text()) != "unreachable"
    ) {
      $("#spinner").show();
    } else {
      $("#spinner").hide();
    }

    $(document).on("contentLoaded", function () {
      $("#spinner").hide();
    });

    if (ipAddress) {
      $.getJSON(`/ajax/get-ping-data/?ip_address=${ipAddress}`)
        .done(function (data) {
          if (data.error) {
            console.log(data.error);
          } else {
            console.log("result:", data);
            $statusIndicator.text(data.result ? "Reachable" : "Unreachable");
            if (data.result) {
              $statusIndicator
                .removeClass("text-danger")
                .addClass("text-success");
              $status.val("connected");
            } else {
              $statusIndicator
                .removeClass("text-success")
                .addClass("text-danger");
              $status.val("disconnected");
            }
            $("#spinner").hide();
          }
        })
        .fail(function (jqXHR, textStatus, errorThrown) {
          console.error("Error fetching ping data:", errorThrown);
        });
    } else {
      alert("Please enter an IP address.");
    }
  });

  // Add PC
  $addPCbutton.on("click", function (e) {
    e.preventDefault();
    $PCformDiv.attr("hidden", false);
    // Clear form
    $("#pc_id").val("");
    $("#id_name").val("");
    $("#id_ip_address").val("");
    $("#id_status").val("");
    $("#id_system_condition").val("");
    $("#form-title").text("Add a PC");
    $addPCbutton.addClass("bg-warning");
    $(".edit-row").click(function () {
      $addPCbutton.removeClass("bg-warning");
    });
    $cancelButton.show();
  });

  $(".edit-row").click(function () {
    let id = $(this).data("pc-id");
    let name = $(this).data("name");
    let ip = $(this).data("ip");
    let status = $(this).data("status");
    let health = $(this).data("health");
    
    // Fill the form fields
    $PCformDiv.attr("hidden", false);
    $statusIndicator.text("");
    $("#pc_id").val(id);
    $("#id_name").val(name);
    $("#id_ip_address").val(ip);
    $("#id_status").val(status);
    $("#id_system_condition").val(health);
    
    // Change title & button
    $("#form-title").text("Edit PC");
    $cancelButton.show();
    $("#addPCbutton").attr("class", "btn btn-round btn-secondary shadow menu-button mb-2");
  });

  $("#save-button").click(function () {
    $PCformDiv.attr("hidden", true);
  });

  $cancelButton.click(function () {
    // Clear form
    $("#pc_id").val("");
    $("#id_name").val("");
    $("#id_ip_address").val("");
    $("#id_status").val("");
    $("#id_system_condition").val("");
    $("#form-title").text("Add a PC");
    $PCformDiv.attr("hidden", true);
    $addPCbutton.removeClass("bg-warning");
    $(this).hide();
  });

  let currentUrl = new URL(window.location.href);
  let btn = $("#repair-button");

  // Set initial Filter button text based on URL
  if (currentUrl.searchParams.get("filter") === "repair") {
    btn.addClass("bg-warning");
  }

  btn.on("click", function (e) {
    e.preventDefault();

    if (currentUrl.searchParams.get("filter") === "repair") {
      currentUrl.searchParams.delete("filter");
    } else {
      currentUrl.searchParams.set("filter", "repair");
    }

    window.location.href = currentUrl.toString();
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
