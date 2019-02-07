// Refresh data page without reloading a windows
function refresh(){
    window.setInterval(function(){
     show_wallets();
    }, 30000);
}

// Show info in wallets selector. Initiate workers data and wallet's details depending on chosen wallet
function show_wallets(){

    // Get all user's wallets
    $.getJSON(Flask.url_for("show_wallets"))
    .done(function(data) {

        if($("#selector-items").val() == null){
            // Form a selector of wallets
            var selector = '';
            for(var i = 0; i < data.length; i++) {
                var wallet = data[i];
                wallet = wallet['wallet_address'];
                selector += '<option>' + wallet + '</option>';
            }
            $('#selector-items').html(selector);
        }
        data = [];
        var addr = $( "#selector-items" ).val();

        // Initiate workers details on the first load while no selectios was made
        show_workers(addr);
        show_wallet_data(addr);
        addr = null;
    });

    // Refresh details on wallets change
    $('#selector-items').change(function(){
        $( "select option:selected" ).each(function() {
        var addr = $( this ).text();
        show_workers(addr);
        show_wallet_data(addr);
        });
    });

}

// Show worker's details of the specified address
function show_workers(address){

    var parameters = {
        addr: address
    };

    // Get workers details and algorythm's names
    $.getJSON(Flask.url_for("display_data"),parameters)
    .done(function(data) {

        // If no worker details were found
        if (data == 'no data'){
            worker_info = '0/0';
            content = '';
        }
        else{
            // Show workers data in a table
            var total_workers = data.length;
            var content ='';
            var currently_active = 0;
            for(var i = 0; i < data.length; i++) {

                var worker = data[i];
                var name = worker['worker_name'];
                var accepted = worker['accepted'];
                var rejected = worker['rejected'];
                var diff = worker['diff'];
                var last_seen = worker['last_seen'];
                var suffix = worker['suffix'];
                var algo_name = worker['algo_name'];
                var time = worker['time'];

                // Mark rows in diferent colors by the time a worker was seen
                if(last_seen >= 1 && last_seen < 10){
                    content +='<tr class=inactive>';
                }
                else if(last_seen >= 10){
                    content +='<tr class=inactive_long>';
                }
                else{
                    content += '<tr class=active>';
                    currently_active += 1;
                }

                // Form a row with workers details and delete row button
                content += '<td>' + name + '</td>'
                        + '<td>' + algo_name + '</td>'
                        + '<td>' + accepted + ' ' + suffix + '</td>'
                        + '<td>' + rejected + '</td>'
                        + '<td>' + diff + '</td>'
                        + '<td>' + time + '</td>'
                        + '<td>' + last_seen + '</td>'
                        + '<td>' + '<input type="button" id="delPOIbutton" value="Remove" onclick="deleteIndexRow(this)"/></td>'
                        + '</tr>';
            }
            var worker_info = currently_active + '/' + total_workers;
        }
        worker = [];
        data = [];

        // Push data to page
        $('#body').html(content);
        $('#wallet_workers').html(worker_info);
    });

}

// Show wallet's details of the specified address
function show_wallet_data(address){

        var parameters = {
            addr: address
        };
        $.getJSON(Flask.url_for("give_wallet"),parameters)
        .done(function(data) {
            // reload and redirect to specifield(login) page if session was lost
            if (data['url'] != null){
                document.location = data['url'];
            }
            else{
                // If no wallet details was found
                if (data == 'no data'){
                    profitability_content = '0.0 ';
                    unpaid_balance = '0.0 ';
                }
                else{
                    for(var i = 0; i < data.length; i++) {

                        // Get wallet's details and show it on webpage
                        var wallet = data[i];
                        var profitability_content = wallet['total_profitability'];
                        var unpaid_balance = wallet['unpaid_balance'];
                    }
                }

                $('#wallet_profitability').html(profitability_content);
                $('#wallet_unpaid').html(unpaid_balance);
            }
            // Get exchange rates and show fiat values
            exchange_rates(profitability_content, unpaid_balance);

            data = [];
        });
}

// Get exchange rates and show fiat values by the currency in user profile
function exchange_rates(profitability_content, unpaid_balance){

    $.getJSON(Flask.url_for("give_exchange_rate"))
    .done(function(data) {

        var exchange_rate = data[0]['rate'];
        var exchange_symbol = ' ' + data[0]['symbol'];

        var fiat_current_content = (exchange_rate * profitability_content).toFixed(2);
        fiat_current_content += exchange_symbol;

        var fiat_unpaid_content = (exchange_rate * unpaid_balance).toFixed(2);
        fiat_unpaid_content += exchange_symbol;

        $('#fiat_current').html(fiat_current_content);
        $('#fiat_unpaid').html(fiat_unpaid_content);
    });
}

// User settings
function settings(){


    // Initiate user summary as first default section to show
    currency_selector();

    $('.settings').hide();
    $('.settings.summary').show();
    $('.list-group-item').removeClass('active');
    $('.list-group-item.summary').addClass('active');

    $('#parentSection').show();

    // Initiate wallets settings
    settings_wallets();


    //Show user summary
    $('#sectionSummaryClick').click(function(){


        $('.settings').hide();
        $('.settings.summary').show();

        $('.list-group-item').removeClass('active');
        $('.list-group-item.summary').addClass('active');

    });

    // Show user wallets
    $('#sectionWalletsClick').click(function(){

        $('.settings').hide();
        $('.settings.wallet').show();

        $('.list-group-item').removeClass('active');
        $('.list-group-item.wallets').addClass('active');

    });

    // Show password change form
    $('#sectionPasswordClick').click(function(){

        $('.settings').hide();
        $('.settings.password').show();

        $('.list-group-item').removeClass('active');
        $('.list-group-item.password').addClass('active');
    });
}

// Show users summary
function settngs_summary (){

    $.getJSON(Flask.url_for("give_user"))
    .done(function(data) {
        // reload and redirect to specifield(login) page if session was lost
        if (data['url'] != null){
                document.location = data['url'];
        }
        else{
            var username = data[0]['username'];
            var currency = data[0]['currency'];
            var email = data[0]['email'];
            $('#user_name').html(username);
            $('#currency-selector-items').val(currency).prop('selected', true);
            $('#email_input').val(email);
            //$('#currency-selector-items').val(currency).prop('selected', true);
            //$('#currency-selector-items option[value=currency]').attr('selected','selected');
        }
    });
}

// Wallet' settings, add or remove new addresses
function settings_wallets(){

    $.getJSON(Flask.url_for("show_wallets"))
    .done(function(data) {
        content = '';
        // Show first input box to enter address if none was found
        if(data.length == 0){
            content += '<tr><td><input size=40 type="text" id="button1"/>'
                    + '</td> <td><input type="button" id="delPOIbutton" value="Delete" onclick="deleteRow(this)"/></td></tr>';
        }
        for(var i = 0; i < data.length; i++) {
            var item = data[i];
            var wallet = item['wallet_address'];

            addInputLIne(wallet);
        }
    });
}

// Delete row in wallet settings
function deleteRow(row)
{
    var i=row.parentNode.parentNode.rowIndex;
    document.getElementById('POITable').deleteRow(i);
}

// Delete row in workers on index page by worker name, algo name, wallet address
function deleteIndexRow(row)
{
    var i=row.parentNode.parentNode.rowIndex;

    var cell0 = document.getElementById("table1").rows[i].cells[0].innerHTML;
    var cell1 = document.getElementById("table1").rows[i].cells[1].innerHTML;
    var addr = $("#selector-items").val();

    $.postJSON( Flask.url_for("deleteIndexRows"), { address: addr, worker: cell0, algo : cell1 } );

    document.getElementById('table1').deleteRow(i);
}

// Insert empty row in wallet settings
function addInputLIne(value=""){

    var rows= $('.address_row').length;

    // Maximu number of addresses allowed
    if(rows < 6){
        $("#POITable").append($("#POITable").find("#address_row").clone().removeAttr("id").find("#addr").val(value).end());
    }
    else{
        alerts('Allowed addresses are limited to: 5', 'alert alert-danger');
    }
}

// Update user wallet addresses after user input in settings
function update_wallets(){

    var addresses = '';

    // Get list of addresses user inputed in a form
    $("#POITable").find('tr').each(function () {
        var $tds = $(this).find('#addr'),
            address = $tds.eq(0).val();

            if (address != ''){
                addresses += address + ',';
            }

    });
    // Remove last comma
    addresses = addresses.slice(0, -1);

    var parameters = {
        addr1: addresses
    };
    $.getJSON(Flask.url_for("update_wallets"),parameters)
    .done(function(data, textStatus, jqXHR) {
        if (data['url'] != null){
            document.location = data['url'];
        }
        else{
            // Show notification about successful update
            alerts('Wallets successfully updated', 'alert alert-success');
        }

    });
}

// Update user wallet addresses after user input in settings
function change_pass(){

    var current_pass = $("#current_password").val();
    var new1_pass = $("#new_password_1").val();
    var new2_pass = $("#new_password_2").val();


    // Pass data to the server for a password change
    $.postJSON( Flask.url_for("change_password"), { current_password: current_pass, new_password_1: new1_pass, new_password_2 : new2_pass })

    // Notify a user about the result of password change
    .done(function(data) {
        if (data['status'] == 'Password was successfully updated'){
            alerts(data['status'], 'alert alert-success');
        }
        else{
            alerts(data['status'], 'alert alert-danger');
        }
        $("#current_password").val('');
        $("#new_password_1").val('');
        $("#new_password_2").val('');
    });
}

// Extend jquery, add JSON data support for jquerry post
jQuery.extend({

    postJSON: function( url, data, callback, type ) {
		// shift arguments if data argument was omited
	    if ( jQuery.isFunction( data ) ) {
			type = type || callback;
			callback = data;
			data = {};
		}

        return jQuery.ajax({
            'type': 'POST',
            'url': url,
            'contentType': 'application/json',
            'data': JSON.stringify(data),
            'dataType': 'json',
            'success': callback

		});
	}
});

// Show notifications for the user after performed actions
function alerts(alertmsg, alertClass){

    $('#alerts').html(alertmsg);
    $('#alerts').attr('class', alertClass);
    $("#alerts").fadeTo(2000, 500).slideUp(500, function(){
        $("#alerts").slideUp(500);
    });
}

function currency_selector(){

    $.getJSON(Flask.url_for("give_currency"))
        .done(function(data) {

            // Form a selector of currencies
            var selector = '';
            for(var i = 0; i < data.length; i++) {
                var currency = data[i];
                currency = currency['currency'];
                selector += '<option>' + currency + '</option>';
            }
            $('#currency-selector-items').html(selector);
            //After data was retrieved generate user settings
            settngs_summary();
        });
}

// Update user wallet addresses after user input in settings
function update_summary(){

    var currency = $('#currency-selector-items').val();
    var email = $('#email_input').val();

    // Pass data to the server for a password change
    $.postJSON( Flask.url_for("update_summary"), { currency: currency, email: email })

    // Notify a user about the result of password change
    .done(function(data) {
        if (data['status'] == 'User profile successfully updated.'){
            alerts(data['status'], 'alert alert-success');
        }
        else{
            alerts(data['status'], 'alert alert-danger');
        }
    });
}