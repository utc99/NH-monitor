//var content;

function show_workers(){

        $.getJSON(Flask.url_for("display_data"))
        .done(function(data, textStatus, jqXHR) {
            total_workers = data.length;
            content ='';
            current_active = 0;
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

                if(last_seen >= 1 && last_seen < 10){
                    content +='<tr class=inactive>';
                }
                else if(last_seen >= 10){
                    content +='<tr class=inactive_long>';
                }
                else{
                    content += '<tr class=active>';
                    current_active += 1;
                }
                content += '<td>' + name + '</td>'
                        + '<td>' + algo_name + '</td>'
                        + '<td>' + accepted + ' ' + suffix + '</td>'
                        + '<td>' + rejected + '</td>'
                        + '<td>' + diff + '</td>'
                        + '<td>' + time + '</td>'
                        + '<td>' + last_seen + '</td>'
                        + '</tr>';

            }
            active_workers = current_active;
            worker_info = current_active + '/' + total_workers;

            $('#body').html(content);
            $('#wallet_workers').html(worker_info);


        });

        show_wallet_data();

}

function show_wallet_data(){
        $.getJSON(Flask.url_for("give_wallet"))
        .done(function(data, textStatus, jqXHR) {
            if (data['url'] != null){
                document.location = data['url'];
            }
            else{
                for(var i = 0; i < data.length; i++) {

                    var wallet = data[i];
                    var wallet_content = wallet['wallet_address'];
                    var profitability_content = wallet['total_profitability'];
                    var unpaid_balance = wallet['unpaid_balance'];
                    console.log(wallet);
                    console.log(unpaid_balance);
                    $('#wallet_profitability').html(profitability_content);
                    $('#address').html(wallet_content);
                    $('#wallet_unpaid').html(unpaid_balance);
                }
            }

            $.getJSON(Flask.url_for("give_exchange_rate"))
            .done(function(data2, textStatus, jqXHR) {

            var exchange_rate = data2[0]['rate'];
            $('#fiat_current').html((exchange_rate * profitability_content).toFixed(2));
            $('#fiat_unpaid').html((exchange_rate * unpaid_balance).toFixed(2));
            });
        });


}
function refresh(){
    window.setInterval(function(){
     show_workers();
    }, 60000);
}