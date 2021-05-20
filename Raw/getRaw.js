function getData() {
  Logger.log("Starting the fetch Process")
  var master_id = '1ShoBS_CPHui4tgtHuYM9KOR3diegqoUuEOR9tUaghg-eg';
  var trip_tracker_id = '16BraPT4BMTZZu_8q7DxqlZYIITXjgnb3MUR5GEB5Qo4';
  var charge_tracker_id = '1Lq519W-aIu9kERUwDr1Z6W0xIjChPk7WSf58wM5ZWw';
  var park_tracker_id = '1rvgmptBj0Yec7m6-E8V-Mdnv3HI2Fm0Y0qnuwjsnY';
  
  var today_mm_ss = Utilities.formatDate(new Date(), 'America/New_York', "dd-MM-yy hh:mm:ss a");
  var today = Utilities.formatDate(new Date(), 'America/New_York', "yyMMdd");
  var yest = Utilities.formatDate(new Date((new Date()).getTime()-1*(24*3600*1000)), 'America/New_York', "yyMMdd");  
  
  var base_url = 'https://owner-api.teslamotors.com/api/1/vehicles/'
  
  var auth_token = "Bearer <token>"
  
  var response = UrlFetchApp.fetch(base_url, {
    'headers':{
      Authorization:auth_token
    },
    muteHttpExceptions:true
  });
  
  if (response.getResponseCode() == 401) {
    MailApp.sendEmail('<email>', 'tesla api auth failed', 'tesla api auth failed');
  }
  Logger.log("tesla api auth success")  
  var data = JSON.parse(response.getContentText());
  
  data.response.forEach(function( d ) {
    Logger.log("getting details for " + d.display_name)
    var name = d.display_name
    
    //***VEHICLE STATE***
    var url = base_url + d.id_s + '/vehicle_data';
    var vehicle_response = UrlFetchApp.fetch(url, {
      'headers':{
        Authorization:auth_token
      },
      muteHttpExceptions:true
    });
    
    var vehicle_data = JSON.parse(vehicle_response);
    
    var res = vehicle_data.response;
    
    let map = new Map();
    map.set("date",today_mm_ss);
    
    for (const [key, value] of Object.entries(res)) {
      if(value != null){
        if(typeof value == "object"){
          for (const [ch_key, ch_value] of Object.entries(value)) {
            map.set(key + "_" + ch_key, ch_value);
          }
        }
        else{
          map.set(key, value);
        }
      }
    }
    
    var sheet = SpreadsheetApp.openById(master_id);
    //Create new sheet for new Car Name if it doesn't already exist
    try {
      sheet.setActiveSheet(sheet.getSheetByName(name + "_" + today));
    } catch (e) {  
      Logger.log("Creating Today's Master Sheet")
      sheet.insertSheet(name + "_" + today);
      
      Logger.log("Deleting Yest Master Sheet")
      var sheet_yest = sheet.getSheetByName(name + "_" + yest);
      sheet.deleteSheet(sheet_yest);
    }
    
    //setting the flags
    var isCharging = 0;
    var isTriping = 0;
    var isDayEnd = false;
    var isEvent = false;
    
    Logger.log("writting the data to Master sheet")
    var a_sheet = sheet.getActiveSheet();
    
    var data = sheet.getDataRange().getValues();
    var row_index = data.length + 1
    for (let [key, value] of map.entries()) {
      var col_index = data[0].indexOf(key);
      if (col_index == -1){
        a_sheet.getRange(1,data[0].length + 1,1,1).setValue(key)
        a_sheet.getRange(row_index, data[0].length + 1).setValue(value)
        var data = sheet.getDataRange().getValues();
      }else{
        a_sheet.getRange(row_index, col_index + 1).setValue(value)
      }
    }
    Logger.log("Write to master completed")
    
    var data = sheet.getDataRange().getValues();
    var last_row = sheet.getLastRow(); //last populated row in sheet
    var last_col = sheet.getLastColumn(); // last populated column in sheet
    
    //getting index of all the important cols
    var charge_state_col_index = data[0].indexOf("charge_state_charging_state") + 1;
    var odometer_col_index = data[0].indexOf("vehicle_state_odometer") + 1;
    var timestamp_col_index = data[0].indexOf("vehicle_state_timestamp") + 1;
    var longitude_col_index = data[0].indexOf("drive_state_longitude") + 1;
    var latitude_col_index = data[0].indexOf("drive_state_latitude") + 1;
    var ideal_battery_range_col_index = data[0].indexOf("charge_state_ideal_battery_range") + 1;
    var energy_added_col_index = data[0].indexOf("charge_state_charge_energy_added") + 1;
    var battery_range_col_index = data[0].indexOf("charge_state_battery_range") + 1;
    var miles_added_ideal_col_index = data[0].indexOf("charge_state_charge_miles_added_ideal") + 1;
    var miles_added_rated_col_index = data[0].indexOf("charge_state_charge_miles_added_rated") + 1;
    var est_battery_range_col_index = data[0].indexOf("charge_state_est_battery_range") + 1;
    var usable_battery_level_col_index = data[0].indexOf("charge_state_usable_battery_level") + 1;
    var battery_level_col_index = data[0].indexOf("charge_state_battery_level") + 1;
    var temp_col_index = data[0].indexOf("climate_state_outside_temp") + 1;
    var user_present_index = data[0].indexOf("vehicle_state_is_user_present") + 1;
    var sentry_mode_index = data[0].indexOf("vehicle_state_sentry_mode") + 1;
    var charge_voltage = data[0].indexOf("charge_state_charger_voltage") + 1;
    
    var prev_row_index = data.length - 1;
    var latest_row_index = data.length;
    
    //fetching current values
    var v_timestamp = a_sheet.getRange(latest_row_index, timestamp_col_index).getValues();
    var latest_charge_state = a_sheet.getRange(latest_row_index, charge_state_col_index).getValues();
    var latest_odometer = a_sheet.getRange(latest_row_index, odometer_col_index).getValues();
    var v_longitude = a_sheet.getRange(latest_row_index, longitude_col_index).getValues();
    var v_latitude = a_sheet.getRange(latest_row_index, latitude_col_index).getValues();
    var v_ideal_battery_range = a_sheet.getRange(latest_row_index, ideal_battery_range_col_index).getValues();
    var v_energy_added = a_sheet.getRange(latest_row_index, energy_added_col_index).getValues();
    var v_battery_range = a_sheet.getRange(latest_row_index, battery_range_col_index).getValues();
    var v_miles_added_ideal = a_sheet.getRange(latest_row_index, miles_added_ideal_col_index).getValues();
    var v_miles_added_rated = a_sheet.getRange(latest_row_index, miles_added_rated_col_index).getValues();
    var v_est_battery_range = a_sheet.getRange(latest_row_index, est_battery_range_col_index).getValues();
    var v_usable_battery_level = a_sheet.getRange(latest_row_index, usable_battery_level_col_index).getValues();
    var v_battery_level = a_sheet.getRange(latest_row_index, battery_level_col_index).getValues();
    var v_temp = a_sheet.getRange(latest_row_index, temp_col_index).getValues();
    var v_user_present = a_sheet.getRange(latest_row_index, user_present_index).getValues();
    var v_sentry_mode = a_sheet.getRange(latest_row_index, sentry_mode_index).getValues();
    var v_charge_voltage = a_sheet.getRange(latest_row_index, charge_voltage).getValues();
    
    //fetching prev values
    var previous_charge_state = a_sheet.getRange(prev_row_index, charge_state_col_index).getValues();
    var previous_odometer = a_sheet.getRange(prev_row_index, odometer_col_index).getValues();
    var previous_user_present = a_sheet.getRange(prev_row_index, user_present_index).getValues();
	var previous_charge_voltage = a_sheet.getRange(prev_row_index, charge_voltage).getValues();
    
    Logger.log("Checking charging session")
    Logger.log("latest charging State = " + latest_charge_state[0][0])
    Logger.log("previous charging State = " + previous_charge_state[0][0])
    
    //Charging Session update
    if(latest_charge_state[0][0] == "Charging" && previous_charge_state[0][0] != "Charging"){
      //session started
      Logger.log("charging session started")
      var sheet_charge = SpreadsheetApp.openById(charge_tracker_id);
      var a_sheet = sheet_charge.getActiveSheet();
      var data = sheet_charge.getDataRange().getValues();
      var log_time = v_timestamp[0];
      a_sheet.appendRow([
        data.length,
        today,
        log_time[0],
        latest_odometer[0][0],
        v_longitude[0][0],
        v_latitude[0][0],
        v_ideal_battery_range[0][0],
        v_energy_added[0][0],
        v_battery_range[0][0],
        v_miles_added_ideal[0][0],
        v_miles_added_rated[0][0],
        v_est_battery_range[0][0],
        v_usable_battery_level[0][0],
        v_battery_level[0][0]      
      ]);
      isCharging = 1;	
      isEvent = true;
    }
    
    if(previous_charge_state[0][0] == "Charging" && latest_charge_state[0][0] != "Charging"){
      Logger.log("charging session completed")
      var sheet_charge = SpreadsheetApp.openById(charge_tracker_id);
      var a_sheet = sheet_charge.getActiveSheet();
      var data = sheet_charge.getDataRange().getValues();
      var log_time = v_timestamp[0]
      a_sheet.getRange(data.length,15,1,1).setValue(latest_odometer[0])
      a_sheet.getRange(data.length,16,1,1).setValue(v_longitude[0])
      a_sheet.getRange(data.length,17,1,1).setValue(v_latitude[0])
      a_sheet.getRange(data.length,18,1,1).setValue(v_ideal_battery_range[0])
      a_sheet.getRange(data.length,19,1,1).setValue(v_energy_added[0])
      a_sheet.getRange(data.length,20,1,1).setValue(v_battery_range[0])
      a_sheet.getRange(data.length,21,1,1).setValue(v_miles_added_ideal[0])
      a_sheet.getRange(data.length,22,1,1).setValue(v_miles_added_rated[0])
      a_sheet.getRange(data.length,23,1,1).setValue(v_est_battery_range[0])
      a_sheet.getRange(data.length,24,1,1).setValue(v_usable_battery_level[0])
      a_sheet.getRange(data.length,25,1,1).setValue(v_battery_level[0])
      a_sheet.getRange(data.length,26,1,1).setValue(log_time[0])
      a_sheet.getRange(data.length,27,1,1).setValue(previous_charge_voltage[0])
      isCharging = -1;
      isEvent = true;
    }
    
    //trip update
    Logger.log("Checking trip details")
    Logger.log("latest odometer = " + latest_odometer[0][0])
    Logger.log("previous odometer = " + previous_odometer[0][0])
    
    
    if(previous_odometer[0][0] < latest_odometer[0][0]){
      //getting the active charge session
      var sheet_charge = SpreadsheetApp.openById(charge_tracker_id);
      var a_sheet = sheet_charge.getActiveSheet();
      var data = sheet_charge.getDataRange().getValues();
      var charge_session_id = data.length - 1;	
      
      var trip_sheet = SpreadsheetApp.openById(trip_tracker_id);
      var a_sheet = trip_sheet.getActiveSheet();
      var data = trip_sheet.getDataRange().getValues();
      Logger.log("values at index 16= " + data[data.length - 1][16])
      if(data[data.length - 1][16] != ""){
        Logger.log("trip started")
        //start trip
        var log_time = v_timestamp[0]
        a_sheet.appendRow([
          data.length,
          today,
          charge_session_id,
          log_time[0],
          latest_odometer[0][0],
          v_longitude[0][0],
          v_latitude[0][0],
          v_ideal_battery_range[0][0],
          v_energy_added[0][0],
          v_battery_range[0][0],
          v_miles_added_ideal[0][0],
          v_miles_added_rated[0][0],
          v_est_battery_range[0][0],
          v_usable_battery_level[0][0],
          v_battery_level[0][0],
          v_temp[0][0]
        ]);
        isTriping = 1
        isEvent = true;
      }
    }
    
    Logger.log("Is user Present = " + v_user_present[0][0])
    
    if(v_user_present[0][0] != true){
      // update the end time with : timestamp
      var trip_sheet = SpreadsheetApp.openById(trip_tracker_id);
      var a_sheet = trip_sheet.getActiveSheet();
      var data = trip_sheet.getDataRange().getValues();
      
      Logger.log("values at index 15= " + data[data.length - 1][15])
      Logger.log("values at index 16= " + data[data.length - 1][16])
      
      if(data[data.length - 1][16] == "" && data[data.length - 1][15] != ""){
        Logger.log("Trip finished")  
        var log_time = v_timestamp[0]
        a_sheet.getRange(data.length,17,1,1).setValue(latest_odometer[0])
        a_sheet.getRange(data.length,18,1,1).setValue(v_longitude[0])
        a_sheet.getRange(data.length,19,1,1).setValue(v_latitude[0])
        a_sheet.getRange(data.length,20,1,1).setValue(v_ideal_battery_range[0])
        a_sheet.getRange(data.length,21,1,1).setValue(v_energy_added[0])
        a_sheet.getRange(data.length,22,1,1).setValue(v_battery_range[0])
        a_sheet.getRange(data.length,23,1,1).setValue(v_miles_added_ideal[0])
        a_sheet.getRange(data.length,24,1,1).setValue(v_miles_added_rated[0])
        a_sheet.getRange(data.length,25,1,1).setValue(v_est_battery_range[0])
        a_sheet.getRange(data.length,26,1,1).setValue(v_usable_battery_level[0])
        a_sheet.getRange(data.length,27,1,1).setValue(v_battery_level[0])
        a_sheet.getRange(data.length,28,1,1).setValue(v_temp[0])
        a_sheet.getRange(data.length,29,1,1).setValue(log_time[0])
        isTriping = -1
        isEvent = true;
      }
    }
    
    //Get the date of the last row of phantom table
    var park_sheet = SpreadsheetApp.openById(park_tracker_id);
    var a_sheet = park_sheet.getActiveSheet();
    var data = park_sheet.getDataRange().getValues();
    var last_date = data[data.length - 1][1].toString()
    
    if (last_date != today){
      Logger.log("New day flag set")  
      isDayEnd = true;
    }
    
    
    //parking tracker
    Logger.log("Is triping = " + isTriping)
    Logger.log("Is charging = " + isCharging)
    Logger.log("Is day end = " + isDayEnd)
    
    if(isTriping == 1 || isCharging == 1 || isDayEnd == true){
      
      // update the end time with : timestamp
      Logger.log("checking Park session")
      var park_sheet = SpreadsheetApp.openById(park_tracker_id);
      var a_sheet = park_sheet.getActiveSheet();
      var data = park_sheet.getDataRange().getValues();
      
      Logger.log("values at index 16= " + data[data.length - 1][16].toString())
      Logger.log("values at index 17= " + data[data.length - 1][17])
      
      if(data[data.length - 1][17] == "" && data[data.length - 1][16].toString() != ""){
        Logger.log("Ending Park session")  
        var log_time = v_timestamp[0]
        a_sheet.getRange(data.length,18,1,1).setValue(latest_odometer[0])
        a_sheet.getRange(data.length,19,1,1).setValue(v_longitude[0])
        a_sheet.getRange(data.length,20,1,1).setValue(v_latitude[0])
        a_sheet.getRange(data.length,21,1,1).setValue(v_ideal_battery_range[0])
        a_sheet.getRange(data.length,22,1,1).setValue(v_energy_added[0])
        a_sheet.getRange(data.length,23,1,1).setValue(v_battery_range[0])
        a_sheet.getRange(data.length,24,1,1).setValue(v_miles_added_ideal[0])
        a_sheet.getRange(data.length,25,1,1).setValue(v_miles_added_rated[0])
        a_sheet.getRange(data.length,26,1,1).setValue(v_est_battery_range[0])
        a_sheet.getRange(data.length,27,1,1).setValue(v_usable_battery_level[0])
        a_sheet.getRange(data.length,28,1,1).setValue(v_battery_level[0])
        a_sheet.getRange(data.length,29,1,1).setValue(v_temp[0])
        a_sheet.getRange(data.length,30,1,1).setValue(log_time[0])
        isEvent = true;
      }
    }
    
    
    //if(isTriping == -1 || isCharging == -1){
    //getting the active charge session
    var sheet_charge = SpreadsheetApp.openById(charge_tracker_id);
    var a_sheet = sheet_charge.getActiveSheet();
    var cdata = sheet_charge.getDataRange().getValues();
    var charge_session_id = cdata.length - 1;
    
    var trip_sheet = SpreadsheetApp.openById(trip_tracker_id);
    var a_sheet = trip_sheet.getActiveSheet();
    var tdata = trip_sheet.getDataRange().getValues();
    
    
    var parkgin_sheet = SpreadsheetApp.openById(park_tracker_id);
    var a_sheet = parkgin_sheet.getActiveSheet();
    var pdata = parkgin_sheet.getDataRange().getValues();
    
    Logger.log("park data values at index 17= " + pdata[pdata.length - 1][17])
    Logger.log("charge data values at index 14= " + cdata[cdata.length - 1][14])
    Logger.log("trip data values at index 16= " + tdata[tdata.length - 1][16])
    
    if((pdata[pdata.length - 1][17] != "") && (cdata[cdata.length - 1][14] != "") && (tdata[tdata.length - 1][16] != "")){
      
      //start parking
      Logger.log("Stating Park session")  
      var log_time = v_timestamp[0]
      a_sheet.appendRow([
        pdata.length,
        today,
        charge_session_id,
        log_time[0],
        latest_odometer[0][0],
        v_longitude[0][0],
        v_latitude[0][0],
        v_ideal_battery_range[0][0],
        v_energy_added[0][0],
        v_battery_range[0][0],
        v_miles_added_ideal[0][0],
        v_miles_added_rated[0][0],
        v_est_battery_range[0][0],
        v_usable_battery_level[0][0],
        v_battery_level[0][0],
        v_temp[0][0],
        v_sentry_mode[0][0]
      ]);
      isEvent = true;
    }
    //}
    
    if(isEvent == true){
      var sheet = SpreadsheetApp.openById(master_id);
      sheet.setActiveSheet(sheet.getSheetByName(name + "_" + today));
      var a_sheet = sheet.getActiveSheet();
      var range = a_sheet.getRange(last_row,1,1,last_col); //gets the range corresponding with the last populated row in the sheet
      range.setBackground("green");
    }
    
    
    
    Logger.log("write completed")
    
  });
  
}
