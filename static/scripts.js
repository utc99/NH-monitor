//var content;

function show_workers(){

        $.getJSON(Flask.url_for("display_data"))
        .done(function(data, textStatus, jqXHR) {
            total_workers = data.length;
            content ='';
            current_active = 0;
            for(var i = 0; i < data.length; i++) {

                    console.log(data[i]);
                    var worker = data[i];
                    var name = worker['worker_name'];
                    var accepted = worker['accepted'];
                    var rejected = worker['rejected'];
                    var diff = worker['diff'];
                    var last_seen = worker['last_seen'];
                    var suffix = worker['suffix'];
                    var algo_name = worker['algo_name'];
                    var time = worker['time'];

                    console.log(accepted);
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
                    content += '<td>' + name+'</td><td>' + algo_name +'</td><td>' + accepted + ' ' + suffix +'</td><td>' +rejected +'</td><td>' +diff +'</td><td>' +time +'</td><td>' + last_seen +'</td></tr>';

            }
            active_workers = current_active;
            worker_info = current_active + '/' + total_workers;
            console.log(content);
            $('#body').html(content);
            $('#wallet_workers').html(worker_info);


        });

        show_wallet_data();

}

function get_wallet(){
        $.getJSON(Flask.url_for("give_wallet"))
        .done(function(data, textStatus, jqXHR) {
            if (data['url'] != null){
                document.location = data['url'];
            }
            else{
                for(var i = 0; i < data.length; i++) {

                    wallet = data[i];
                    content = wallet['wallet_address'];
                    content += '</br>     -     Total profitability: ';
                    content += wallet['total_profitability'];

                    $('#address').html(content);
                }
            }
        });
}

function show_wallet_data(){
        $.getJSON(Flask.url_for("give_wallet"))
        .done(function(data, textStatus, jqXHR) {
            if (data['url'] != null){
                document.location = data['url'];
            }
            else{
                for(var i = 0; i < data.length; i++) {

                    wallet = data[i];
                    wallet_content = wallet['wallet_address'];
                    profitability_content = wallet['total_profitability'];

                    $('#wallet_profitability').html(profitability_content);
                    $('#address').html(wallet_content);
                }
            }
        });
}
function refresh(){
    window.setInterval(function(){
     show_workers();
    }, 60000);
}