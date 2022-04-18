function getToken() {
  Logger.log("Geting the latest token")
  var master_id = '';
  var sheet = SpreadsheetApp.openById(master_id);
  var a_sheet = sheet.getActiveSheet();
  return a_sheet.getDataRange().getValues()[0][0]
}

function getVehLst(base_url){
  Logger.log("getting the Veh lst")
  var response = UrlFetchApp.fetch(base_url, {
    'headers':{
      Authorization:"Bearer " + getToken()
    },
    muteHttpExceptions:true
  });

  return response;
}

function getVehicleData(base_url,map){
  Logger.log("getting veh details")
    var vehicle_response = UrlFetchApp.fetch(base_url, {
      'headers':{
        Authorization:"Bearer " + getToken()
      },
      muteHttpExceptions:true
    });

    return vehicle_response;
}

function writeDataToMaster(res,master_id,today,yest,map){
  Logger.log("fetching the veh details and creating a map")
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

  Logger.log("Create new sheet for new Car Name if it doesn't already exist")
  var sheet = SpreadsheetApp.openById(master_id);
  
    try {
      sheet.setActiveSheet(sheet.getSheetByName(today));
    } catch (e) { 
      Logger.log("Creating Today's Master Sheet")
      sheet.insertSheet(today);

      var sheet_yest = sheet.getSheetByName(yest);
      
      Logger.log("Archiving Yest Master Sheet")
      var ssNew = SpreadsheetApp.create(yest);
      sheet_yest.copyTo(ssNew);
      
      Logger.log("Deleting Yest Master Sheet")
      sheet.deleteSheet(sheet_yest);
    }

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

}

function chkDateChanged(last_event){
  Logger.log("checking if the day has endded")
  var is_new_date = false
  var curr_ts = new Date()
  var curr_date = Utilities.formatDate(curr_ts, 'America/New_York', "yyMMdd");

  Logger.log("current date :" + curr_date)
  var last_event_ts = new Date(last_event)
  var last_event = Utilities.formatDate(last_event_ts, 'America/New_York', "yyMMdd");

  Logger.log("last event date :" + last_event)

  if (last_event != curr_date){
    Logger.log("date chenged") 
    is_new_date = true;
  }

  return is_new_date
}

function endEvent(sheet,data,eventName,startIndex){
  Logger.log("stoping the event")
  col_lst = []

  if(eventName == 'trip'){
    trip_end_time = data.vehicle_state.timestamp 
    trip_end_odometer = data.vehicle_state.odometer
    trip_end_ideal_battery_range = data.charge_state.ideal_battery_range 
    trip_end_battery_level = data.charge_state.battery_level
    trip_end_temp = data.climate_state.outside_temp
    col_lst = [trip_end_time,trip_end_odometer,trip_end_ideal_battery_range,trip_end_battery_level,trip_end_temp]
  }else if(eventName == 'charge'){
    session_end_time = data.vehicle_state.timestamp
    session_end_energy_added = data.charge_state.charge_energy_added
    session_end_miles_added_ideal = data.charge_state.charge_miles_added_ideal
    session_end_odometer = data.vehicle_state.odometer
    col_lst = [session_end_time,session_end_energy_added,session_end_miles_added_ideal,session_end_odometer]
  }else{
    park_end_time = data.vehicle_state.timestamp
    park_end_battery_level = data.charge_state.usable_battery_level
    park_end_ideal_battery_range = data.charge_state.ideal_battery_range
    park_end_temp = data.climate_state.outside_temp
    col_lst = [park_end_time,park_end_battery_level,park_end_ideal_battery_range,park_end_temp]
  }
  var sheetdata = sheet.getDataRange().getValues();

  writeData(startIndex,col_lst,sheet,sheetdata.length);
}

function startEvent(sheet,data,eventName){
  Logger.log("Starting the event")
  var sheetdata = sheet.getDataRange().getValues();
  var col_data = []

  if(eventName == 'trip'){
    trip_id = sheetdata.length
    trip_start_time = data.vehicle_state.timestamp 
    trip_start_odometer = data.vehicle_state.odometer
    trip_start_ideal_battery_range = data.charge_state.ideal_battery_range 
    trip_start_battery_level = data.charge_state.battery_level
    trip_start_temp = data.climate_state.outside_temp
    charge_sheetId = '1k3MtPPhL4qw8ghi65QSCZcLVRkdZv-GjUHO2V0ZAKZQ';
    var charge_sheet = SpreadsheetApp.openById(charge_sheetId);
  var charge_sheet_active = sheet.getActiveSheet();
    var charge_sheetdata = charge_sheet_active.getDataRange().getValues();
    charge_sessionID = sheetdata.length



    col_data = [trip_id,trip_start_time,trip_start_odometer,trip_start_ideal_battery_range,trip_start_battery_level,trip_start_temp,charge_sessionID]
  }else if(eventName == 'charge'){
    session_id = sheetdata.length
    session_start_time = data.vehicle_state.timestamp
    charge_voltage = data.charge_state.charger_voltage
    session_start_energy_added = data.charge_state.charge_energy_added
    session_start_miles_added_ideal = data.charge_state.charge_miles_added_ideal
    session_start_odometer = data.vehicle_state.odometer
    col_data = [session_id,session_start_time,charge_voltage,session_start_energy_added,session_start_miles_added_ideal,session_start_odometer]
  }else{
    park_id = sheetdata.length
    park_start_time = data.vehicle_state.timestamp
    park_start_battery_level = data.charge_state.usable_battery_level
    park_start_ideal_battery_range = data.charge_state.ideal_battery_range
    park_start_temp = data.climate_state.outside_temp
    sentry_mode = data.vehicle_state.sentry_mode
    col_data = [park_id,park_start_time,park_start_battery_level,park_start_ideal_battery_range,park_start_temp,sentry_mode]
  }

  writeData(0,col_data,sheet,sheetdata.length + 1);

}

function writeData(startIndex,col_lst,sheet,rowId){
  for (var counter = startIndex; counter <= startIndex + col_lst.length; counter = counter + 1) {
    sheet.getRange(rowId,counter+1,1,1).setValue(col_lst[counter-startIndex])
  }
}

function validateandUpdateSheet(sheetName,action,newData){
  var sheetId = "";
  var end_index = 0;
  var isDateChanged = false;

  if(sheetName =="trip"){
    sheetId = '1WJj_cyybNDVTV6-OnXuiwEUhJ42DxFfawpCxHgzMPzo';
    end_index = 6
  }else if(sheetName =="charge"){
    sheetId = '1k3MtPPhL4qw8ghi65QSCZcLVRkdZv-GjUHO2V0ZAKZQ';
    end_index = 6
  }else{
    sheetId = '1rA1Tx7s73FuodjAsDkFbNk4UhQM9YdlC5JgH0LNHVKA';
    end_index = 5
  }

  var sheet = SpreadsheetApp.openById(sheetId);
  var a_sheet = sheet.getActiveSheet();
  var data = sheet.getDataRange().getValues();
  
  Logger.log("checking if previous " + sheetName + " currently active")
  if(data[data.length - 1][end_index] == ""){
    Logger.log("event is active")
    if(chkDateChanged(data[data.length - 1][1])){
      endEvent(a_sheet,newData,sheetName)
    }else{
      if(action == "start"){
        Logger.log("do nothing")
        return
      }else{
        endEvent(a_sheet,newData,sheetName,end_index)   
      }
    }
  }
  else{
    Logger.log("event is not active")
    if(action == "stop"){
      Logger.log("do nothing")
      return
    }else{
      startEvent(a_sheet,newData,sheetName)
    }
  }
}

function getDataV2() {
  Logger.log("Starting the fetch Process")
  var master_id = '1ShoBS_CPHui4tgtHuYM9KOR3diegqoUuEOR9tUag-eg';
  
  
  var date = new Date()

  var today_mm_ss = Utilities.formatDate(date, 'America/New_York', "dd-MM-yy hh:mm:ss a");
  var today = Utilities.formatDate(date, 'America/New_York', "yyMMdd");
  var yest = Utilities.formatDate(new Date((date).getTime()-1*(24*3600*1000)), 'America/New_York', "yyMMdd");

  let map = new Map();
  map.set("date",today_mm_ss);

  var base_url = 'https://owner-api.teslamotors.com/api/1/vehicles/'
  var response = getVehLst(base_url)
  
  if (response.getResponseCode() == 401) {
    MailApp.sendEmail('nautiyal.sarthak@gmail.com', 'tesla api auth failed', 'tesla api auth failed');
  }

  Logger.log("tesla api auth success")  
  
  var data = JSON.parse(response.getContentText());
  data.response.forEach(function( d ) {
    Logger.log("getting details for " + d.display_name)
    var name = d.display_name
  
    var url = base_url + d.id_s + '/vehicle_data';
    var vehicle_response = getVehicleData(url,map);
    
    var vehicle_data = JSON.parse(vehicle_response);
    var res = vehicle_data.response;
    var drivestate = res.drive_state.shift_state
    var charge_state = res.charge_state.charging_state

    if(drivestate == "D"){
      Logger.log("Car is currently being driven")
      validateandUpdateSheet("trip","start",res)
      validateandUpdateSheet("charge","stop",res)
      validateandUpdateSheet("park","stop",res)
    }
    else if (charge_state == "Charging"){
      Logger.log("Car is currently being charged")
      validateandUpdateSheet("charge","start",res)
      validateandUpdateSheet("trip","stop",res)
      validateandUpdateSheet("park","stop",res)
    }
    else{
      Logger.log("Car is currently parked")
      validateandUpdateSheet("park","start",res)
      validateandUpdateSheet("charge","stop",res)
      validateandUpdateSheet("trip","stop",res)
    }
  });
  
}
