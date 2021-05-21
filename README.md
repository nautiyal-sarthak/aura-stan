This dashboard was bacically created to understand my car better and the effects of temprature on a EV. 
The car will only be in one of the three states : 

1. In a trip
2. Parked
3. Charging

keeping this information in mind lets get in the code :

This app is broadly split into two sub applications 

1. Raw : Responsible for fetching the data from tesla api every 1 min and then persisting the state in google sheets. 
2. Standarised + UI : Responsible for reading the google sheets , calcualte the kpis and finally draw the various graphs etc.

