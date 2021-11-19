# odoo_sms_manager_jasmin

  These modules are used to send and receive sms messages from a jasmin SMS gateway.
  They are used to be as a module for the Odoo ERP system and are integrated with its functionalities.
  
How to Install
  You will need first to install the dependancies for the SMS_Manager module
which are web_notify (version-13.0.1.0.0) and kanban_draggable(version -1.0)
After that first install the SMS_manager module and then the calendar and CRM moudle( 
they obviously need Calendar and CRM modules ).
How to Use
  You first need to set a user permission in the settings as jasmin sms user 
Then Create a jasmin sms gateway configurate (add username,password,type(SMPP or HTTP))
For SMPP in the url section input IP:PORT, For HTTP input the default jasmin http route for sending messages.
 then you are ready to send sms messages.
 example - http://127.0.0.1:1401/send   for HTTP
           127.0.0.1:2775 for SMPP
 
  For sending Campign messages the code will take the ip address from the url depending on te type of gateway 
  and will add the default rest api url parameters set by the jasmin framework and make a request.
  example http://127.0.0.1:8080/secure/balance - for restful only ip will be different based on the gateway input
  
  TO send Messages
    select a contact, press action ,press send to contact
    select a company, press action, press send to copany employee
    create a campign choose your type and gateway , send the message
    select a calender event, press action, press send to attendees
    select a CRM, press action, press send to company
    
    
    
    Note.. If dependancies can not e found, i have them in my local files please send me a message 
    kalebteshale72@gmail.com
     https://t.me/Kaleb_iii
