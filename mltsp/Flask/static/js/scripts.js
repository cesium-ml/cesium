function draw_charts_and_plots(prediction_entry_key, source_fname){

                        $.get("/load_source_data/" + String(prediction_entry_key) + "/" + String(source_fname), function(data){

                                var features_dict = data['features_dict'];

                                // plot ts data:
                                var tmag = [];
                                console.log(data['ts_data'][0].length);
                                if(data['ts_data'][0].length==3){
                                        var plot_errs = true;
                                }else{
                                        var plot_errs = false;
                                }
                                for (var i=0; i < data['ts_data'].length; i++){
                                        if (plot_errs==true){
                                                tmag.push([parseFloat(data['ts_data'][i][0]), parseFloat(data['ts_data'][i][1]), parseFloat(data['ts_data'][i][1])-parseFloat(data['ts_data'][i][2]), parseFloat(data['ts_data'][i][1])+parseFloat(data['ts_data'][i][2])]);
                                        }else{
                                                tmag.push([parseFloat(data['ts_data'][i][0]), parseFloat(data['ts_data'][i][1])]);
                                        }

                                }
                                var ts_data = new google.visualization.DataTable();
                                ts_data.addColumn('number','Time');
                                ts_data.addColumn('number','Magnitude');
                                if(plot_errs==true){
                                        ts_data.addColumn({type:'number', role:'interval'});
                                        ts_data.addColumn({type:'number', role:'interval'});
                                }
                                ts_data.addRows(tmag);

                                var ts_data_plot_options = {title:"Time series data", hAxis:{title:"time"}, vAxis:{title:"magnitude", direction:-1}, legend: 'none', explorer: {actions:['dragToZoom','rightClickToReset']}, intervals: { style: 'bars', barWidth:0.05, lineWidth:0.6, color:"#b20000", fillOpacity: 0.7}, pointSize:5, lineWidth:0, dataOpacity: 0.7}

                                var chart = new google.visualization.LineChart(document.getElementById('ts_data_plot_div'));
                                chart.draw(ts_data, ts_data_plot_options);






                                // compute and plot phase-folded ts data if period has been computed:
                                var period = 0;
                                if("freq1_harmonics_freq_0" in features_dict){
                                        console.log("period = " + String(1.0/parseFloat(features_dict["freq1_harmonics_freq_0"])));
                                        period=1.0/parseFloat(features_dict["freq1_harmonics_freq_0"]);
                                        var phase_mag = [];
                                        for (var i=0; i < data['ts_data'].length; i++){

                                                var phase = (parseFloat(data['ts_data'][i][0])/period)%1;
                                                if(plot_errs==true){
                                                        phase_mag.push([phase, parseFloat(data['ts_data'][i][1]), parseFloat(parseFloat(data['ts_data'][i][1])-parseFloat(data['ts_data'][i][2])), parseFloat(parseFloat(data['ts_data'][i][1])+parseFloat(data['ts_data'][i][2]))]);
                                                }else{
                                                        phase_mag.push([phase, parseFloat(data['ts_data'][i][1])]);
                                                }
                                        }

                                        var folded_ts_data = new google.visualization.DataTable();
                                        folded_ts_data.addColumn('number','Phase');
                                        folded_ts_data.addColumn('number','Magnitude');
                                        if(plot_errs=true){
                                                folded_ts_data.addColumn({type:'number', role:'interval'});
                                                folded_ts_data.addColumn({type:'number', role:'interval'});
                                        }
                                        folded_ts_data.addRows(phase_mag);

                                        var folded_ts_data_plot_options = {title:"Period-folded time series data (Period = "+String(period).substring(0,7) + ")", hAxis:{title:"phase"}, vAxis:{title:"magnitude", direction:-1}, legend: 'none', explorer: {actions:['dragToZoom','rightClickToReset']}, intervals: { style: 'bars', barWidth:0.05, lineWidth:0.6, color:"#b20000", fillOpacity: 0.7}, pointSize:5, lineWidth:0, dataOpacity: 0.7}

                                        var chart = new google.visualization.LineChart(document.getElementById('ts_data_folded_plot_div'));
                                        chart.draw(folded_ts_data, folded_ts_data_plot_options);

                                }else{
                                        console.log("freq1_harmonics_freq_0 not in features_dict");
                                        $('#ts_data_folded_plot_div').html("<h5>Period-folded time series data plot</h5><BR><BR><h4>freq1_harmonics_freq_0 (frequency) not computed for this feature set.</h4>");
                                }








                                // build features table:
                                for (var key in features_dict){
                                        $("#features_table tbody").append("<tr><td>"+String(key)+"</td><td>"+String(features_dict[key]).substring(0,9)+"</td></tr>");
                                }






                                // draw chart showing P_Class for top classes:
                                var pred_results_for_chart = [["Class","Probability"]];
                                var pred_results = data['pred_results'];
                                var num_classes_in_chart = 3;
                                if (pred_results.length < num_classes_in_chart){
                                        num_classes_in_chart = pred_results.length; }
                                for (var i=0; i < num_classes_in_chart; i++){
                                        pred_results_for_chart.push(pred_results[i]);
                                }
                                var pred_results_datatable = google.visualization.arrayToDataTable(pred_results_for_chart);
                                var pred_results_chart_options = {title:"Top class prediction results", orientation:"horizontal", legend:'none', vAxis: {title: "Probability", minValue: 0}, hAxis: {title: "Class name"} };

                                var chart2 = new google.visualization.BarChart(document.getElementById('pred_results_bar_chart_div'));
                                chart2.draw(pred_results_datatable, pred_results_chart_options);








                        });
                }









function check_job_status(PID){

        var status_msg = $.ajax({
                type: "POST",
                url: "/check_job_status/?PID="+String(PID),
                async: false
        }).responseText;

        return String(status_msg);

}







function bind_pred_results_fname_cells(pred_entry_key){
        $(".pred_results_fname_cell").click( function(){
                window.open("/source_details/"+pred_entry_key+"/"+$(this).text(), "_blank");
        });
}






function uploadFeaturesFormDialog(){

        var $uploadFeaturesFormDialog = $("<div id='uploadFeaturesFormDialog' class='editDeleteResultsDialog'></div>")
                .html("File must conform to the following formatting guidelines:...<BR><BR>\
                                        <form id='uploadFeaturesForm' name='uploadFeaturesForm' action='/uploadFeaturesForm' enctype='multipart/form-data' method='post'>\
                                                <table>\
                                                        <tr>\
                                                                <td><label>Project name:</label></td>\
                                                                <td><select id='featureset_projname_select' name='featureset_projname_select'></select></td>\
                                                        </tr>\
                                                        <tr><td><label>Feature set name:</label></td><td><input type='text' id='featuresetname' name='featuresetname'><div id='featsetname_okay_div' name='featsetname_okay_div'></div></td></tr>\
                                                        <tr><td><label>Select features file:</label></td>\
                                                                <td><input type='file' id='features_file' name='features_file' class='stylized_input'></td>\
                                                        </tr>\
                                                        <tr>\
                                                                <td align='center' colspan=2><input type='submit' value='Submit' id='uploadfeaturesbutton' name='uploadfeaturesbutton'></td>\
                                                        </tr>\
                                                </table>\
                                        </form>")
                .dialog({
                        autoOpen: true,
                        title: 'Upload Features File',
                        width:500,
                        height:300,
                        close: function(event,ui){ $(this).dialog('destroy').remove(); }//,
                        //buttons: [{text:"Submit",click:function(){$(this).dialog("close"); $(this).dialog("destroy"); document.getElementById("uploadFeaturesForm").submit();}}]
                });
        $.get("/get_list_of_projects", function(data){
                populate_select_options('featureset_projname_select',data['list']);
        });




        if( $("#featureset_projname_select").length > 0 && $("#featureset_projname_select").val() != null && $("#featureset_projname_select").val() != "null"){
                $.get("/get_list_of_featuresets_by_project/"+String($("#featureset_projname_select").val()), function(data){
                        var selected_project_featureset_names = data['featset_list'];
                        enforce_unique_name('uploadfeaturesbutton','featuresetname','featsetname_okay_div',selected_project_featureset_names);
                }); }

        $("#featureset_projname_select").change( function(){

                $.get("/get_list_of_featuresets_by_project/"+String($("#featureset_projname_select").val()), function(data){
                        var selected_project_featureset_names = data['featset_list'];
                        enforce_unique_name('uploadfeaturesbutton','featuresetname','featsetname_okay_div',selected_project_featureset_names);
                });
        });


}





function editOrDeleteProjectFormSubmit(){

        if($("#action").val()=="Delete"){
                var x = confirm("Delete selected project?");
                if(x==false){
                        return false;
                }
        }


        $("#editOrDeleteProjectForm").ajaxSubmit({
                clearForm: false,
                success:
                        function( response ){


                                if($("#action").val()=="Delete"){

                                        var $editDeleteResultsDialog = $('<div id="editDeleteResultsDialog" class="editDeleteResultsDialog"></div>')
                                                .html(response["result"])
                                                        .dialog({
                                                                autoOpen: true,
                                                                title: 'Request Response',
                                                                buttons: [{text:"Ok",click: function(){ $(this).dialog("close"); } }]
                                                                //position: ['center', 20]
                                        });

                                        $("#editDeleteResultsDialog").bind("dialogclose", function(event){
                                                window.location.replace("http://"+location.host);
                                        });

                                }else if($("#action").val()=="Edit"){

                                        var $editDeleteResultsDialog = $('<div id="editDeleteResultsDialog" class="editDeleteResultsDialog"></div>')
                                                .html("<form id='editProjectForm' name='editProjectForm' action='/editProjectForm' enctype='multipart/form-data' method='post'> \
                                                                <table> \
                                                                        <tr> \
                                                                                <td align='left'> \
                                                                                        <label>Project Name</label> \
                                                                                </td> \
                                                                                <td align='left' colspan=4> \
                                                                                        <div><input type='text' name='project_name_edit' id='project_name_edit' class='stylized_input' size='30' value='"+response['name']+"'><input type='hidden' name='project_name_orig' id='project_name_orig' value='"+response['name']+"'></div><div id='edit_proj_name_okay_div' name='edit_proj_name_okay_div'></div> \
                                                                                </td> \
                                                                        </tr> \
                                                                        <tr> \
                                                                                <td align='left'> \
                                                                                        <label>Created</label> \
                                                                                </td> \
                                                                                <td align='left' colspan=4> \
                                                                                        <div><input type='text' name='date_created' id='date_created' class='stylized_input' size='50' value='"+response['created']+"' disabled> \
                                                                                </td> \
                                                                        </tr> \
                                                                        <tr> \
                                                                                <td align='left'> \
                                                                                        <label>Description/notes</label> \
                                                                                </td> \
                                                                                <td colspan=4> \
                                                                                        <textarea id='project_description_edit' name='project_description_edit' rows='3' cols='50'>"+response['description']+" </textarea> \
                                                                                </td> \
                                                                        </tr> \
                                                                        <tr> \
                                                                                <td align='left'> \
                                                                                        <label>Additional Authorized Users<span class='small'>Enter Google account usernames <br>(separated by a comma) of <br>those you wish to have access to this project</span></label> \
                                                                                </td> \
                                                                                <td colspan=4> \
                                                                                        <textarea id='addl_authed_users_edit' name ='addl_authed_users_edit' rows='3' cols='50'>" + response['authed_users'].join() + "</textarea> \
                                                                                </td> \
                                                                                <td> \
                                                                                </td> \
                                                                        </tr> \
                                                                        <tr> <td><BR></td></tr><tr>\
                                                                                <td align='left' colspan=3> \
                                                                                        <div onclick=\"$('#features_table').toggle('slow');\"><label>Feature sets (click to show/hide table):</label></div> \
                                                                                </td> \
                                                                        </tr> \
                                                                </table> \
                                                                        " + response['featuresets'] + " \
                                                                <table><tr> <td><BR></td></tr><tr> \
                                                                                <td align='left' colspan=3> \
                                                                                        <div onclick=\"$('#models_table').toggle('slow');\"><label>Models (click to show/hide table):</label></div> \
                                                                                </td> \
                                                                        </tr> \
                                                                </table> \
                                                                        " + response['models'] + " \
                                                                <table><tr> <td><BR></td></tr><tr>\
                                                                                <td align='left' colspan=3> \
                                                                                        <div onclick=\"$('#predictions_table').toggle('slow');\"><label>Predictions (click to show/hide table):</label></div> \
                                                                                </td> \
                                                                        </tr> \
                                                                </table> \
                                                                        " + response['predictions'] + " \
                                                        </form>")
                                                        .dialog({
                                                                height:700,
                                                                width:850,
                                                                autoOpen: true,
                                                                title: 'Edit Project Details',
                                                                buttons: [{text:"Submit", click:
                                                                        function(){


                                                                                if($.trim($("#project_name_edit").val())==""){
                                                                                        alert("Project Name must contain non-whitespace characters. Please try another name.");
                                                                                }else{


                                                                                        $("#editProjectForm").ajaxSubmit({
                                                                                                success: function(editResponse){

                                                                                                        var $projectEditedDialog = $('<div id="projectEditedDialog" class="projectEditedDialog"></div>')
                                                                                                                .html("Project info saved.")
                                                                                                                        .dialog({
                                                                                                                                autoOpen: true,
                                                                                                                                buttons:[{text: "Ok", click: function(){ $("#projectEditedDialog").dialog("close"); } } ]
                                                                                                                                //position: ['center', 20]
                                                                                                        });

                                                                                                        $("#projectEditedDialog").bind("dialogclose", function(event){
                                                                                                                window.location.replace("http://"+location.host);
                                                                                                        });

                                                                                                        $("#editDeleteResultsDialog").dialog("destroy").remove();
                                                                                                }
                                                                                        });
                                                                                }
                                                                        }
                                                                }]
                                                                //position: ['center', 20]
                                        });

                                        $(".feats_used_div").dialog({autoOpen: false, maxHeight: 650, width: 500 } );
                                        $(".pred_results_dialog_div").dialog({autoOpen: false, maxHeight: 650, width:600} );
                                        $("#editDeleteResultsDialog").bind("dialogclose", function(event){
                                                $("#editDeleteResultsDialog").dialog("destroy").remove();
                                        });

                                        $.get("/get_list_of_projects", function(data){
                                                var current_projects=data['list'];
                                                current_projects.splice(current_projects.indexOf(response['name']),1);
                                                enforce_unique_name('edit_project_button','project_name_edit','edit_proj_name_okay_div',current_projects);
                                        });


                                }


                        }
        });
}

















function newProjectFormSubmit(){
        $("#newProjectForm").ajaxSubmit({
                clearForm: false,
                success: function(response){

                                var $newProjectAddedDialog = $('<div id="newProjectAddedDialog" class="newProjectAddedDialog"></div>')
                                        .html(response["result"])
                                                .dialog({
                                                        autoOpen: true,
                                                        title: 'Request Response',
                                                        buttons:[{text: "Ok", click: function(){ $("#newProjectAddedDialog").dialog("close"); } } ]
                                                        //position: ['center', 20]
                                });

                                $("#newProjectAddedDialog").bind("dialogclose", function(event){
                                        window.location.replace("http://"+location.host);
                                });

                        }

        });

}









function populate_select_options(select_id,option_vals_list){
        var $selector = $("#"+select_id);
        $selector.empty().append(function(){
                var optionval = "";
                $.each(option_vals_list, function(index){
                        var optiontxt = option_vals_list[index];
                        if(optiontxt.indexOf(" meta_feats=") != -1){
                                var meta_feats_str = optiontxt.split(" meta_feats=")[1];
                                optiontxt = optiontxt.split(" meta_feats=")[0];
                                var title_str = " title='" + meta_feats_str + "'";
                        }else{
                                var meta_feats_str = false;
                                var title_str = "";
                        }
                        optionval += "<option value='" + optiontxt + "'" + title_str + ">" + optiontxt + "</option>"
                });
                return optionval;
        }).change();

}

function prediction_metadata_required_validate(TrueOrFalse){


        if(TrueOrFalse==true){

                $("#newpred_file").unbind("change");
                $("#newpred_file").change(function(){
                        var metadata_filename = $("#prediction_files_metadata").val();
                        var tsdata_filename = $("#newpred_file").val();
                        if(metadata_filename=="" || tsdata_filename==""){
                                $('#predict_form_submit_button').attr('disabled','disabled');
                        }else{
                                $('#predict_form_submit_button').removeAttr('disabled');
                        }
                });


                var metadata_filename = $("#prediction_files_metadata").val();
                var tsdata_filename = $("#newpred_file").val();
                if(metadata_filename=="" || tsdata_filename==""){
                        $('#predict_form_submit_button').attr('disabled','disabled');
                }else{
                        $('#predict_form_submit_button').removeAttr('disabled');
                }
                $("#prediction_files_metadata").change(function(){
                        var metadata_filename = $("#prediction_files_metadata").val();
                        var tsdata_filename = $("#newpred_file").val();
                        if(metadata_filename=="" || tsdata_filename==""){
                                $('#predict_form_submit_button').attr('disabled','disabled');
                        }else{
                                $('#predict_form_submit_button').removeAttr('disabled');
                        }
                });
        }else{
                predict_form_validation();
        }
}





function pred_model_select_change(){

        var meta_feats_str = $("#prediction_model_name_and_type option:selected").attr("title");
        if (typeof meta_feats_str !== "undefined" && meta_feats_str !== false){

                $('#metadata_required_msg_td').html("<font color='red'>A header file providing the following metadata features is required for this model: " + meta_feats_str + "</font>");
                $('#metadata_required_msg_tr').fadeIn();
                $('#predict_metadata_tr').fadeIn();
                prediction_metadata_required_validate(true);
        }else{
                $('#predict_metadata_tr').fadeOut();
                $('#metadata_required_msg_tr').fadeOut();
                prediction_metadata_required_validate(false);
        }
}







function enforce_unique_name(button_id,text_field_id,msg_div_id,names_list){

        $("#"+button_id).attr('disabled','disabled');

        if($.trim($('#'+text_field_id).val()) != '') {
                if(names_list.indexOf($.trim($('#'+text_field_id).val())) == -1){

                        $('#'+msg_div_id).html('');
                        if(button_id=="featurize_button"){
                                featurize_form_validation();
                        }else if(button_id=="uploadfeaturesbutton"){
                                if($("#features_file").val()!=""){
                                        $('#'+button_id).removeAttr('disabled');
                                }
                        }else{
                                $('#'+button_id).removeAttr('disabled');
                        }
                }else{
                        if(button_id.indexOf("feat") == -1){
                                $('#'+msg_div_id).html('<font size=1 color="red">Another project with this name already exists.</font>');
                        } else {
                                $('#'+msg_div_id).html('<font size=1 color="red">Another feature set with this name already exists.</font>');
                        }
                        $('#'+button_id).attr('disabled','disabled');
                }
        } else {
                $('#'+button_id).attr('disabled','disabled');
                $('#'+msg_div_id).html('');
        }



        $('#'+text_field_id).bind("keyup change input", function() {
                if($.trim($(this).val()) != '') {
                        if(names_list.indexOf($.trim($(this).val())) == -1){
                                $('#'+msg_div_id).html('');
                                if(button_id=="featurize_button"){
                                        featurize_form_validation();
                                }else if(button_id=="uploadfeaturesbutton"){
                                        if($("#features_file").val()!=""){
                                                $('#'+button_id).removeAttr('disabled');
                                        }
                                }else{
                                        $('#'+button_id).removeAttr('disabled');
                                }
                        } else {
                                if(button_id.indexOf("feat") == -1){
                                        $('#'+msg_div_id).html('<font size=1 color="red">Another project with this name already exists.</font>');
                                } else {
                                        $('#'+msg_div_id).html('<font size=1 color="red">Another feature set with this name already exists.</font>');
                                }
                                $('#'+button_id).attr('disabled','disabled');
                        }
                } else {
                        $('#'+button_id).attr('disabled','disabled');
                        $('#'+msg_div_id).html('');
                }
        });
}





function resetFormElement(e){
        e.wrap("<form>").closest("form").get(0).reset();
        e.unwrap();

}





function featurizeFormSubmit(){

        $("#model_build_results").html("<img src='/static/media/spinner_black.gif'> Uploading files...");

        $("#featurizeForm").ajaxSubmit({
                success: function(response){

                        if("type" in response){
                                if(response["type"]=="error"){
                                        var is_error = true;
                                }else{
                                        var is_error = false;
                                }

                        }else{
                                var is_error = false;
                        }

                        if(is_error==true){

                                alert(response["message"]);
                                $("#model_build_results").html(response["message"]);

                                resetFormElement($("#headerfile"));
                                resetFormElement($("#zipfile"));



                        }else{

                                var PID = response["PID"];
                                var featureset_name = response["featureset_name"];
                                var featureset_key = response["featureset_key"];
                                var project_name = response["project_name"];
                                var headerfile_name = response["headerfile_name"];
                                var zipfile_name = response["zipfile_name"];


                                window.location.replace("http://"+location.host+"/featurizing?PID="+PID+"&featureset_key="+featureset_key+"&project_name="+project_name+"&featureset_name="+featureset_name);

                        }

                }
        });


}






function predictFormSubmit(){

        $("#class_pred_results").html("<img src='/static/media/spinner_black.gif'> Processing your request...");

        $("#model_build_results").hide();
        $("#class_pred_results").show();

        $("#predictForm").ajaxSubmit({
                success: function(response){

                        if("type" in response){
                                if(response["type"]=="error"){
                                        var is_error = true;
                                }else{
                                        var is_error = false;
                                }
                        }else{
                                var is_error = false;
                        }

                        if(is_error==true){

                                alert(response["message"]);
                                $("#class_pred_results").html(response["message"]);

                                resetFormElement($("#newpred_file"));
                                resetFormElement($("#prediction_files_metadata"));


                        }else{
                                var PID = response["PID"];
                                var prediction_entry_key = response["prediction_entry_key"];
                                var project_name = response["project_name"];
                                var model_name = response["model_name"];
                                var model_type = response["model_type"];

                                window.location.replace("http://"+location.host+"/predicting?PID="+PID+"&prediction_entry_key="+prediction_entry_key+"&project_name="+project_name+"&prediction_model_name="+model_name+"&model_type="+model_type);

                        }
                }
        });

}






function buildModelFormSubmit(){
        $("#class_pred_results").html("<img src='/static/media/spinner_black.gif'> Processing your request...");

        $("#model_build_results").hide();
        $("#class_pred_results").show();

        $("#buildModelForm").ajaxSubmit({
                success: function(response){

                        //alert(response["message"]);

                        var PID = response["PID"];
                        var new_model_key = response["new_model_key"];
                        var project_name = response["project_name"];
                        var model_name = response["model_name"];

                        window.location.replace("http://"+location.host+"/buildingModel?PID="+PID+"&new_model_key="+new_model_key+"&project_name="+project_name+"&model_name="+model_name);

                }
        });

}






function plotFeaturesFormSubmit(){
        project_name = $( "#plot_feats_project_name_select" ).val();
        featureset_name = $( "#plot_features_featset_name_select" ).val();
        $.get("/get_featureset_id_by_projname_and_featsetname/"+project_name+"/"+featureset_name,function(data){
                drawScatterplotMatrix("/static/data/" + data["featureset_id"] + "_features_with_classes.csv");
        });
        $('#tabs').tabs( "option", "active",  false);
}









// OBSOLETE:
function get_lc_data(){

        var data2 = $.get('/getLcData', function(data){
                $("#lc_plot").empty();

                if($("#show_errors_checkbox").is(':checked')){
                        var show_error_bars = true; }
                else{
                        var show_error_bars = false; }


                var dataarr = new Array(data);
                var datapts = eval(dataarr[0]);
                if (datapts[0].length == 2){
                        var has_errors = false;
                }else if(datapts[0].length == 3){
                        var has_errors = true;
                }else{
                        var has_errors = false;
                }

                var options = {
                                        series: {
                                                lines: { show: false },
                                                points: { show: true }
                                                        },
                };
                if(has_errors==true){
                        var data1_points_options = {
                                fill: false,
                                errorbars: "y",
                                yerr: {show: show_error_bars, color: "red", upperCap: "-", lowerCap: "-"}
                        };
                }else{
                        var data1_points_options = {
                                fill: false
                        };
                }

                var data2 = [{color: "blue", points: data1_points_options, data: datapts, label:"Light Curve"}];

                return data2;
        });

        return data2;

}




// OBSOLETE:
function plot_light_curve(){
        $.get('/getLcData', function(data){

                $("#lc_plot").empty();

                if($("#show_errors_checkbox").is(':checked')){
                        var show_error_bars = true; }
                else{
                        var show_error_bars = false; }


                var dataarr = new Array(data);
                var datapts = eval(dataarr[0]);
                if (datapts[0].length == 2){
                        var has_errors = false;
                }else if(datapts[0].length == 3){
                        var has_errors = true;
                }else{
                        var has_errors = false;
                }

                var y_min = datapts[0][1];
                var y_max = datapts[0][1];
                for(var i=1; i<datapts.length; i++){
                        if(datapts[i][1] > y_max){
                                y_max = datapts[i][1]; }
                        if(datapts[i][1] < y_min){
                                y_min = datapts[i][1]; }
                }


                var options = {
                                        legend: { show: false },
                                        series: {
                                                lines: { show: false },
                                                points: { show: true },
                                                        },
                                        yaxis: { min: y_min, max: y_max, transform: function (v) { return -v; }, inverseTransform: function (v) { return -v; } },
                                        selection: { mode: "xy" }
                };


                if(has_errors==true){
                        var data1_points_options = {
                                fill: false,
                                errorbars: "y",
                                yerr: {show: show_error_bars, color: "red", upperCap: "-", lowerCap: "-"}
                        };
                }else{
                        var data1_points_options = { fill: false };
                }

                var data2 = [{color: "blue", points: data1_points_options, data: datapts, label:"Mag/Flux vs Time"}];

                // initial plot
                var plot = $.plot($("#lc_plot"),data2,options);



                // setup overview
                var overview = $.plot($("#overview"), data2, {
                        legend: { show: true, container: $("#overviewLegend") },
                        series: {
                                lines: { show: false },
                                points: { show: true },

                                shadowSize: 0
                        },
                        xaxis: { ticks: 3 },
                        yaxis: { min: y_min, max: y_max, transform: function (v) { return -v; }, inverseTransform: function (v) { return -v; } },
                        grid: { color: "#999" },
                        selection: { mode: "xy" }
                });

                // now connect the two

                $("#lc_plot").bind("plotselected", function (event, ranges) {
                        // clamp the zooming to prevent eternal zoom
                        if (ranges.xaxis.to - ranges.xaxis.from < 0.00001)
                                ranges.xaxis.to = ranges.xaxis.from + 0.00001;
                        if (ranges.yaxis.to - ranges.yaxis.from < 0.00001)
                                ranges.yaxis.to = ranges.yaxis.from + 0.00001;

                        // do the zooming
                        plot = $.plot($("#lc_plot"), data2,
                                                  $.extend(true, {}, options, {
                                                          xaxis: { min: ranges.xaxis.from, max: ranges.xaxis.to },
                                                          yaxis: { min: ranges.yaxis.from, max: ranges.yaxis.to, transform: function (v) { return -v; }, inverseTransform: function (v) { return -v; } }
                                                  }));

                        // don't fire event on the overview to prevent eternal loop
                        overview.setSelection(ranges, true);
                });
                $("#overview").bind("plotselected", function (event, ranges) {
                        plot.setSelection(ranges);
                });



        });

}



// OBSOLETE:
function draw_lines_avgerr_vs_cadsmed(avg_err, cads_med){
        var x_equals_0 = 38.0; // from left edge
        var x_equals_10 = 652.0;
        var y_equals_0 = 361.0; // from top edge
        var y_equals_1 = 17.0;

        var x_scale = (x_equals_10 - x_equals_0)/10.0;
        var y_scale = y_equals_0 - y_equals_1;

        var x_loc = cads_med*x_scale + x_equals_0;
        var y_loc = y_equals_0 - avg_err*y_scale; // from top edge

        $("#canvas1").drawLine({
                strokeStyle: "#F00",
                strokeWidth: 1,
                x1: x_loc-15, x2: x_loc+15,
                y1: y_loc, y2: y_loc
        });

        $("#canvas1").drawLine({
                strokeStyle: "#F00",
                strokeWidth: 1,
                x1: x_loc, x2: x_loc,
                y1: y_loc-15, y2: y_loc+15
        });
}




// OBSOLETE:
function draw_lines_avgdbltosnglstep_vs_cadsstd(avgdbltosnglstep, cads_std){
        var x_equals_0 = 44.0; // from left edge
        var x_equals_100 = 660.0;
        var y_equals_0 = 359.5; // from top edge
        var y_equals_3000 = 21.0;

        var x_scale = (x_equals_10 - x_equals_0)/100.0;
        var y_scale = (y_equals_0 - y_equals_3000)/3000.0;

        var x_loc = cads_std*x_scale + x_equals_0;
        var y_loc = y_equals_0 - avgdbltosnglstep*y_scale; // from top edge

        $("#canvas2").drawLine({
                strokeStyle: "#F00",
                strokeWidth: 1,
                x1: x_loc-15, x2: x_loc+15,
                y1: y_loc, y2: y_loc
        });

        $("#canvas2").drawLine({
                strokeStyle: "#F00",
                strokeWidth: 1,
                x1: x_loc, x2: x_loc,
                y1: y_loc-15, y2: y_loc+15
        });
}



// OBSOLETE:
function draw_lines(avgerr, cadsmed, avgdbltosnglstep, cadsstd){

        draw_lines_avgerr_vs_cadsmed(avgerr,cadsmed);
        draw_lines_avgdbltosnglstep_vs_cadsstd(avgdbltosnglstep, cadsstd);

}




// OBSOLETE:
function feature_images(){
        $("#canvas1").drawImage({
                source: "/static/media/avg_err_vs_cads_med.png",
                x:0, y:0, fromCenter: false
                //height: 600, width: 800,
                //load: draw_lines
        });

        $("#canvas2").drawImage({
                source: "/static/media/avg_dbltosnglstep_vs_cads_std.png",
                x:0, y:0, fromCenter: false
                //height: 600, width: 800,
                //load: draw_lines
        });

}





// OBSOLETE:
function init_blank_plot(){
        var data1 = [[],[],[],[]];

        var data1 = [{color: "blue", points: data1_points_options, data: data1, label: "Mag/Flux vs Time"}];
        var data1_points_options = {
                                fillColor: "blue",
                                errorbars: "y",
                                yerr: {show: true, color: "red", upperCap: "-", lowerCap: "-"}
        };

        var options = {
                legend: { show: false },
                series: {
                        lines: { show: true },
                        points: { show: true,
                                                errorbars: "y",
                                                yerr: { show: true,
                                                        asymmetric: true,
                                                        upperCap: "-",
                                                        lowerCap: "-"
                                                        }
                                        }
                                }
        };


        var plot = $.plot($("#lc_plot"),data1);


        // setup overview
        var overview = $.plot($("#overview"), data1, {
                legend: { show: true, container: $("#overviewLegend") },
                series: {
                        lines: { show: true, lineWidth: 1 },
                        shadowSize: 0
                },
                xaxis: { ticks: 4 },
                yaxis: { ticks: 3, min: -2, max: 2 },
                grid: { color: "#999" },
                selection: { mode: "xy" }
        });

        // now connect the two

        $("#lc_plot").bind("plotselected", function (event, ranges) {
                // clamp the zooming to prevent eternal zoom
                if (ranges.xaxis.to - ranges.xaxis.from < 0.00001)
                        ranges.xaxis.to = ranges.xaxis.from + 0.00001;
                if (ranges.yaxis.to - ranges.yaxis.from < 0.00001)
                        ranges.yaxis.to = ranges.yaxis.from + 0.00001;

                // do the zooming
                plot = $.plot($("#lc_plot"), data1,
                                          $.extend(true, {}, options, {
                                                  xaxis: { min: ranges.xaxis.from, max: ranges.xaxis.to },
                                                  yaxis: { min: ranges.yaxis.from, max: ranges.yaxis.to }
                                          }));

                // don't fire event on the overview to prevent eternal loop
                overview.setSelection(ranges, true);
        });
        $("#overview").bind("plotselected", function (event, ranges) {
                plot.setSelection(ranges);
        });


}





function get_lc_data_filename(filename,sep){
        $("#lcdata").load('/get_lc_data/?filename='+new String(filename)+'&sep='+new String(sep));
}




function featurize_form_validation(){


        var headerfile_name = $("#headerfile").val();
        var zipfile_name = $("#zipfile").val();
        var featset_name = $("#featureset_name").val();
        if(headerfile_name=="" || zipfile_name=="" || $.trim(featset_name)==""){
                $('#featurize_button').attr('disabled','disabled');
        }else{
                $('#featurize_button').removeAttr('disabled');
        }

        $("#headerfile,#zipfile").change(function(){
                var headerfile_name = $("#headerfile").val();
                var zipfile_name = $("#zipfile").val();
                var featset_name = $("#featureset_name").val();
                if(headerfile_name=="" || zipfile_name=="" || $.trim(featset_name)==""){
                        $('#featurize_button').attr('disabled','disabled');
                }else{
                        $('#featurize_button').removeAttr('disabled');
                }
        });
}




function upload_features_form_validation(){

        if($("#features_file").val()=="" || $.trim($("#featuresetname").val())==""){
                $("#uploadfeaturesbutton").attr('disabled','disabled');
        }else{
                $.get("/get_list_of_featuresets_by_project/"+String($("#featureset_projname_select").val()), function(data){
                        var selected_project_featureset_names = data['featset_list'];
                        enforce_unique_name('uploadfeaturesbutton','featuresetname','featsetname_okay_div',selected_project_featureset_names);
                });
        }

        $("#featureset_projname_select,#features_file").change(function(){
                if($("#features_file").val()=="" || $.trim($("#featuresetname").val())==""){
                        $("#uploadfeaturesbutton").attr('disabled','disabled');
                }else{
                        $.get("/get_list_of_featuresets_by_project/"+String($("#featureset_projname_select").val()), function(data){
                                var selected_project_featureset_names = data['featset_list'];
                                enforce_unique_name('uploadfeaturesbutton','featuresetname','featsetname_okay_div',selected_project_featureset_names);
                        });
                }
        });
}






function predict_form_validation(){


        var filename = $("#newpred_file").val();
        if(filename=="" || $("#prediction_model_name_and_type").has('option').length == 0){
                $('#predict_form_submit_button').attr('disabled','disabled');
        }else{
                $('#predict_form_submit_button').removeAttr('disabled');
        }

        $("#newpred_file,#prediction_project_name").change(function(){
                var filename = $("#newpred_file").val();
                if(filename=="" || $("#prediction_model_name_and_type").has('option').length == 0){
                        $('#predict_form_submit_button').attr('disabled','disabled');
                }else{
                        $('#predict_form_submit_button').removeAttr('disabled');
                }
        });
}







function build_model_form_validation(){



        $.get('/get_list_of_models_by_project/'+$("#buildmodel_project_name_select").val(), function(data){
                var model_list = data['model_list'];
                var model_list_shortened = [];
                for(i=0; i++; i<model_list.length){
                        model_list_shortened.push(model_list[i].slice(0,model_list[i].indexOf(" (created")));
                }
                if(model_list_shortened.indexOf($("#modelbuild_featset_name_select").val() + " - " + $("#model_type_select").val())==-1){
                        $('#model_build_submit_button').removeAttr('disabled');
                        $("#model_build_okay_msg_div").html("");
                } else {
                        $('#model_build_submit_button').attr('disabled','disabled');
                        $("#model_build_okay_msg_div").html("<font size=1 color='red'>A model with the selected specifications already exists.</font>");
                }

                if($("#modelbuild_featset_name_select").has('option').length == 0){
                        $('#model_build_submit_button').attr('disabled','disabled');
                }


        });



        $("#buildmodel_project_name_select").add($("#modelbuild_featset_name_select")).add($("#model_type_select")).change(function() {

                $.get('/get_list_of_models_by_project/'+$("#buildmodel_project_name_select").val(), function(data){
                        var model_list = data['model_list'];
                        var model_list_shortened = [];
                        for(i=0; i<model_list.length; i++){
                                model_list_shortened.push(model_list[i].slice(0,model_list[i].indexOf(" (created")));
                        }
                        if(model_list_shortened.indexOf($("#modelbuild_featset_name_select").val() + " - " + $("#model_type_select").val())==-1){
                                $('#model_build_submit_button').removeAttr('disabled');
                                $("#model_build_okay_msg_div").html("");
                        } else {
                                $('#model_build_submit_button').attr('disabled','disabled');
                                $("#model_build_okay_msg_div").html("<font size=1 color='red'>A model with the selected specifications already exists.</font>");
                        }

                        if($("#modelbuild_featset_name_select").has('option').length == 0){
                                $('#model_build_submit_button').attr('disabled','disabled');
                        }

                });
        });



}










function populate_select_options_multiple(){

        if( $("#featureset_project_name_select").length > 0){
                $.get("/get_list_of_featuresets_by_project/"+String($("#featureset_project_name_select").val()), function(data){
                        var selected_project_featureset_names = data['featset_list'];
                        enforce_unique_name('featurize_button','featureset_name','featset_name_okay_div',selected_project_featureset_names);
                }); }

        $("#featureset_project_name_select").change( function(){

                $.get("/get_list_of_featuresets_by_project/"+String($("#featureset_project_name_select").val()), function(data){
                        var selected_project_featureset_names = data['featset_list'];
                        enforce_unique_name('featurize_button','featureset_name','featset_name_okay_div',selected_project_featureset_names);
                });
        });



        if( $("#buildmodel_project_name_select").length > 0) {
                $.get("/get_list_of_featuresets_by_project/"+String($("#buildmodel_project_name_select").val()), function(data){
                        var selected_project_featset_names = data['featset_list'];
                        populate_select_options('modelbuild_featset_name_select',selected_project_featset_names);
                }); }

        $("#buildmodel_project_name_select").change( function(){

                $.get("/get_list_of_featuresets_by_project/"+String($("#buildmodel_project_name_select").val()), function(data){
                        var selected_project_featset_names = data['featset_list'];
                        populate_select_options('modelbuild_featset_name_select',selected_project_featset_names);
                });
        });



        if( $("#plot_feats_project_name_select").length > 0) {
                $.get("/get_list_of_featuresets_by_project/"+String($("#plot_feats_project_name_select").val()), function(data){
                        var selected_project_featset_names = data['featset_list'];
                        populate_select_options('plot_features_featset_name_select',selected_project_featset_names);
                        if($("#plot_features_featset_name_select").has('option').length == 0){
                                $('#plot_features_button').attr('disabled','disabled');
                        }else{
                                $('#plot_features_button').removeAttr('disabled');
                        }
                }); }

        $("#plot_feats_project_name_select").change( function(){

                $.get("/get_list_of_featuresets_by_project/"+String($("#plot_feats_project_name_select").val()), function(data){
                        var selected_project_featset_names = data['featset_list'];
                        populate_select_options('plot_features_featset_name_select',selected_project_featset_names);
                        if($("#plot_features_featset_name_select").has('option').length == 0){
                                $('#plot_features_button').attr('disabled','disabled');
                        }else{
                                $('#plot_features_button').removeAttr('disabled');
                        }
                });
        });




        $.get("/get_list_of_models_by_project/"+String($("#prediction_project_name").val()), function(data){
                var selected_project_model_names = data['model_list'];
                populate_select_options('prediction_model_name_and_type',selected_project_model_names);
        });

        $("#prediction_project_name").change( function(){

                $.get("/get_list_of_models_by_project/"+String($("#prediction_project_name").val()), function(data){
                        var selected_project_model_names = data['model_list'];
                        populate_select_options('prediction_model_name_and_type',selected_project_model_names);
                });
        });

        pred_model_select_change();
        $("#prediction_model_name_and_type").change( function(){
                pred_model_select_change(); });

}







function form_validations(){

        predict_form_validation();

        featurize_form_validation();

        build_model_form_validation();

}





function test_custom_feature_script(){
        /*
        $('body').append('<div style="display:none;"><form id="test_new_script_form" name="test_new_script_form" action="/testNewScript" enctype="multipart/form-data" method="post"></form></div>');
        $("#custom_feat_script_file").appendTo($('#test_new_script_form'));
        console.log($("#custom_feat_script_file").val());
        */
        $("#featurizeForm").attr('action', '/testNewScript');
        fileUpload(document.getElementById('featurizeForm'), "/testNewScript", "file_upload_message_div");


        console.log("Done");


        /*


        $("#test_new_script_form").ajaxForm(function(){
                        alert("Success!");
                }
        );









        $.post("/testNewScript",{custom_feat_script_file:document.getElementById("custom_feat_script_file").files[0]}, function(data){
                alert(data);
        });
        */


}






function fileUpload(form, action_url, div_id) {
    // Create the iframe...
    var iframe = document.createElement("iframe");
    iframe.setAttribute("id", "upload_iframe");
    iframe.setAttribute("name", "upload_iframe");
    iframe.setAttribute("width", "0");
    iframe.setAttribute("height", "0");
    iframe.setAttribute("border", "0");
    iframe.setAttribute("style", "width: 0; height: 0; border: none;");

    // Add to document...
    form.parentNode.appendChild(iframe);
    window.frames['upload_iframe'].name = "upload_iframe";

    iframeId = document.getElementById("upload_iframe");

    // Add event...
    var eventHandler = function () {

            if (iframeId.detachEvent) iframeId.detachEvent("onload", eventHandler);
            else iframeId.removeEventListener("load", eventHandler, false);

            // Message from server...
            if (iframeId.contentDocument) {
                content = iframeId.contentDocument.body.innerHTML;
            } else if (iframeId.contentWindow) {
                content = iframeId.contentWindow.document.body.innerHTML;
            } else if (iframeId.document) {
                content = iframeId.document.body.innerHTML;
            }

            $("#featurizeForm").attr('action', '/uploadDataFeaturize');
            $("#featurizeForm").attr('target', '_self');

            document.getElementById(div_id).innerHTML = content;

            $("#custom_script_tested").val('yes');

            // Del the iframe...
            setTimeout('iframeId.parentNode.removeChild(iframeId)', 250);
        }

    if (iframeId.addEventListener) iframeId.addEventListener("load", eventHandler, true);
    if (iframeId.attachEvent) iframeId.attachEvent("onload", eventHandler);

    // Set properties of form...
    form.setAttribute("target", "upload_iframe");
    form.setAttribute("action", action_url);
    form.setAttribute("method", "post");
    form.setAttribute("enctype", "multipart/form-data");
    form.setAttribute("encoding", "multipart/form-data");
        document.getElementById(div_id).innerHTML = "Testing your script...";
    // Submit the form...
    form.submit();


}









function init_dialogs(){


        var $features_dialog = $('<div id="features" class="features_dialog" title="Features"></div>')
                .html("No features yet...")
                .dialog({
                        height:500,
                        width:600,
                        autoOpen: false,
                        title: 'Time Series Data Features',
                        position: ['center', 20]
                });

        $('#features_link').click(function() {
                $features_dialog.dialog('open');
                // prevent the default action, e.g., following a link
                return false;
        });


        $("#features").bind("clickoutside", function(event){
                $(this).dialog("close");
        });


        var $feature_selection_dialog = $('<div id="feature_selection_dialog" class="feature_selection_dialog" align="left"></div>')
                .html("Using all features for now...")
                .dialog({
                        height:500,
                        width:600,
                        autoOpen: false,
                        title: 'Feature Selection',
                        position: ['center', 20],
                        buttons: [{text:"Done",click:function(){$(this).dialog("close");}}]
                });


        $("#feature_selection_dialog").bind("clickoutside", function(event){
                $(this).dialog("close");
        });


        $('#feature_selection_link').click(function() {
                $feature_selection_dialog.dialog('open');
                // prevent the default action, e.g., following a link
                return false;
        });


        var $predict_metadata_format_dialog = $("<div id='predict_metadata_format_dialog' class='editDeleteResultsDialog'></div>")
                .html("<div align='left'><i>Data must be comma-separated (no spaces). The first line of the csv file must be the names of the features provided (starting with filename) corresponding to those provided in the headerfile of the labeled training data during the featurization step. The following lines contain the data. See the sample format below. </i><br><br><br>filename,meta_feature1_name,meta_feature2_name,meta_feature3_name<br>tsfile_1.dat,C,2.131412,0.3459010<br>tsfile_2.dat,A,11.924581,3.0174719<br>tsfile_2.dat,L,8.0181033,1.2074736<br>...</div>")
                .dialog({
                        autoOpen: false,
                        title: 'Prediction metadata file format',
                        width:550,
                        height:300,
                        buttons: [{text:"Close",click:function(){$(this).dialog("close");}}]
                });

        $("#predict_metadata_format_dialog").bind("clickoutside", function(event){
                $(this).dialog("close");
        });

        $('#predict_metadata_format_dialog_link').click(function() {
                $predict_metadata_format_dialog.dialog('open');
                // prevent the default action, e.g., following a link
                return false;
        });









        var $ts_data_headerfile_format_dialog = $("<div id='ts_data_headerfile_format_dialog' class='editDeleteResultsDialog'></div>")
                .html("<div align='left'><i>Data must be comma-separated (no spaces). The first line of the csv file must be the names of the features provided (starting with filename,class) corresponding to those provided in the headerfile of the labeled training data during the featurization step. The following lines contain the data. See the sample format below. </i><br><br><br>filename,class,meta_feature1_name,meta_feature2_name<br>tsfile_1.dat,Class_C,2.131412,0.3459010<br>tsfile_2.dat,Class_A,11.924581,3.0174719<br>tsfile_2.dat,Class_L,8.0181033,1.2074736<br>...</div>")
                .dialog({
                        autoOpen: false,
                        title: 'Training set headerfile required format',
                        width:550,
                        height:300,
                        buttons: [{text:"Close",click:function(){$(this).dialog("close");}}]
                });

        $("#ts_data_headerfile_format_dialog").bind("clickoutside", function(event){
                $(this).dialog("close");
        });

        $('#ts_data_headerfile_format_dialog_link').click(function() {
                $ts_data_headerfile_format_dialog.dialog('open');
                // prevent the default action, e.g., following a link
                return false;
        });



        var $ts_data_tarball_format_dialog = $("<div id='ts_data_tarball_format_dialog' class='editDeleteResultsDialog'></div>")
                .html("<div align='left'><i>Tarball file must contain a single folder containing all of the individual time series files. </i></div>")
                .dialog({
                        autoOpen: false,
                        title: 'Training set tarball required format',
                        width:500,
                        height:200,
                        buttons: [{text:"Close",click:function(){$(this).dialog("close"); }}]
                });

        $("#ts_data_tarball_format_dialog").bind("clickoutside", function(event){
                $(this).dialog("close");
        });


        $('#ts_data_tarball_format_dialog_link').click(function() {
                $ts_data_tarball_format_dialog.dialog('open');
                // prevent the default action, e.g., following a link
                return false;
        });









        var about_txt = "The UC Berkeley Center For Time-Domain Informatics (departments of Astronomy and Statistics) has developed this site in order to provide a machine learning web service to the wider scientific community. More to come..."
        var $about_dialog = $('<div></div>')
                .html(about_txt)
                .dialog({
                        autoOpen: false,
                        title: 'About'
                });

        $('#about').click(function() {
                $about_dialog.dialog('open');
                // prevent the default action, e.g., following a link
                return false;
        });


        var contact_txt = "Email us at MLTimeseriesPlatform {at} gmail {dot} com."
        var $contact_dialog = $('<div></div>')
                .html(contact_txt)
                .dialog({
                        autoOpen: false,
                        title: 'Contact'
                });

        $('#contact').click(function() {
                $contact_dialog.dialog('open');
                // prevent the default action, e.g., following a link
                return false;
        });
}





function select_deselect_all_feats1(){

        if ($(".feat1_checkbox").length == $(".feat1_checkbox:checked").length){
                $(".feat1_checkbox").prop("checked",false);
        }else{
                $(".feat1_checkbox").prop("checked",true);
        }
}






function select_deselect_all_feats2(){

        if ($(".feat2_checkbox").length == $(".feat2_checkbox:checked").length){
                $(".feat2_checkbox").prop("checked",false);
        }else{
                $(".feat2_checkbox").prop("checked",true);
        }
}














function drawScatterplotMatrix(datafilename){

        $("#visualizationDiv").html("");
        $("#visualizationLegendDiv").html("");


        var width = 920,
    size = 150,
    padding = 15.5;

        var x = d3.scale.linear()
                .range([padding / 2, size - padding / 2]);

        var y = d3.scale.linear()
                .range([size - padding / 2, padding / 2]);

        var xAxis = d3.svg.axis()
                .scale(x)
                .orient("bottom")
                .ticks(5);

        var yAxis = d3.svg.axis()
                .scale(y)
                .orient("left")
                .ticks(5);

        var color = d3.scale.category20();





        d3.csv(datafilename, function(error, dataset) {
          var domainByTrait = {},
                  traits = d3.keys(dataset[0]).filter(function(d) { return d !== "class"; }),
                  n = traits.length;

          traits.forEach(function(trait) {
                domainByTrait[trait] = d3.extent(dataset, function(d) { return d[trait]; });
          });

          xAxis.tickSize(size * n);
          yAxis.tickSize(-size * n);


          var class_list = new Array();
          for(var i=0; i < dataset.length; i++){
                          if ( $.inArray(dataset[i].class, class_list) == -1 ){
                                  class_list.push(dataset[i].class);
                          }
                }
          console.log(class_list);


          var brush = d3.svg.brush()
                  .x(x)
                  .y(y)
                  .on("brushstart", brushstart)
                  .on("brush", brushmove)
                  .on("brushend", brushend);

          var svg = d3.select("#visualizationDiv").append("svg")
                  .attr("width", size * n + padding)
                  .attr("height", size * n + padding)
                .append("g")
                  .attr("transform", "translate(" + padding + "," + padding / 2 + ")");

          svg.selectAll(".x.axis")
                  .data(traits)
                .enter().append("g")
                  .attr("class", "x axis")
                  .attr("transform", function(d, i) { return "translate(" + (n - i - 1) * size + ",0)"; })
                  .each(function(d) { x.domain(domainByTrait[d]); d3.select(this).call(xAxis); });

          svg.selectAll(".y.axis")
                  .data(traits)
                .enter().append("g")
                  .attr("class", "y axis")
                  .attr("transform", function(d, i) { return "translate(0," + i * size + ")"; })
                  .each(function(d) { y.domain(domainByTrait[d]); d3.select(this).call(yAxis); });

          var cell = svg.selectAll(".cell")
                  .data(cross(traits, traits))
                .enter().append("g")
                  .attr("class", "cell")
                  .attr("transform", function(d) { return "translate(" + (n - d.i - 1) * size + "," + d.j * size + ")"; })
                  .each(plot);

          // Titles for the diagonal.
          cell.filter(function(d) { return d.i === d.j; }).append("text")
                  .attr("x", padding)
                  .attr("y", padding)
                  .attr("dy", ".71em")
                  .text(function(d) { return d.x; });

          cell.call(brush);

          function plot(p) {
                var cell = d3.select(this);

                x.domain(domainByTrait[p.x]);
                y.domain(domainByTrait[p.y]);

                cell.append("rect")
                        .attr("class", "frame")
                        .attr("x", padding / 2)
                        .attr("y", padding / 2)
                        .attr("width", size - padding)
                        .attr("height", size - padding);

                cell.selectAll("circle")
                        .data(dataset)
                  .enter().append("circle")
                        .attr("cx", function(d) { return x(d[p.x]); })
                        .attr("cy", function(d) { return y(d[p.y]); })
                        .attr("r", 3)
                        .attr("class", function(d){ return String(d.class); })
                        .style("fill", function(d) { return color(String(d.class)); });
          }

          var brushCell;

          // Clear the previously-active brush, if any.
          function brushstart(p) {
                if (brushCell !== this) {
                  d3.select(brushCell).call(brush.clear());
                  x.domain(domainByTrait[p.x]);
                  y.domain(domainByTrait[p.y]);
                  brushCell = this;
                }
          }

          // Highlight the selected circles.
          function brushmove(p) {
                var e = brush.extent();
                svg.selectAll("circle").classed("hidden", function(d) {
                  return e[0][0] > d[p.x] || d[p.x] > e[1][0]
                          || e[0][1] > d[p.y] || d[p.y] > e[1][1];
                });
          }

          // If the brush is empty, select all circles.
          function brushend() {
                if (brush.empty()){
                        svg.selectAll(".hidden").classed("hidden", false);
                }
          }

          function cross(a, b) {
                var c = [], n = a.length, m = b.length, i, j;
                for (i = -1; ++i < n;) for (j = -1; ++j < m;) c.push({x: a[i], i: i, y: b[j], j: j});
                return c;
          }

          d3.select(self.frameElement).style("height", size * n + padding + 20 + "px");






                var leg_svg = d3.select("#visualizationLegendDiv").append("svg")
                        .attr("width", 100)
                        .attr("height", 800)
                        .append("g");

                var legendGroup = leg_svg.selectAll('.legend').data(class_list).enter().append('g')
                                                 .attr('class', 'legend')
                                                 .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

                var legendEntryRect = legendGroup.append("rect")
                                                        //.attr("class", "legend-entry")
                                                        .attr("x",10)
                                                        .attr('height',10)
                                                        .attr('width',10)
                                                        .style('fill',function(d) { return color(String(d)); })
                                                        .on('mouseover', function(d){
                                                                svg.selectAll("circle").classed("hidden", function(){
                                                                        return d !== d3.select(this).attr('class');
                                                                });
                                                        })
                                                        .on('mouseout', function(){
                                                                svg.selectAll("circle").classed("hidden", false); //function(){ return d3.select(this).attr('class') !== 'brushSelected'; });
                                                        });

                var legendEntryText = legendGroup.append("text")
                                                        //.attr("class", "legend-entry")
                                                        .attr('x',25)
                                                        .attr('y',10)
                                                        .text(function(d){ return d; });


          /*
          var legendGroup = svg.selectAll('.legend').data(class_list).enter().append('g')
                     .attr('class', 'legend')
                     .attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });

        var legendEntryRect = legendGroup.append("rect")
                                                //.attr("class", "legend-entry")
                                                .attr("x",50)
                                                .attr('height',10)
                                                .attr('width',10)
                                                .style('fill',function(d) { return color(String(d)); });

        var legendEntryText = legendGroup.append("text")
                                                //.attr("class", "legend-entry")
                                                .attr('x',65)
                                                .text(function(d){ return d; });
                                                //.attr("transform", function(d, i) { return "translate(0," + i * 20 + ")"; });
                */

        });

}
