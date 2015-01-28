const fileIO        = require("sdk/io/file");
const system        = require("sdk/system");
var socket          = require("./lib/socket.js");

var crawlID = null;

// Read the db address from file
//var path = system.pathFor("ProfD") + '/database_settings.txt';
var path = '/home/sengleha/research/OpenWPM/automation/Extension/openwpm/database_settings.txt';
if (fileIO.exists(path)) {
    var dbstring = fileIO.read(path, 'r').split(',');
    var host = dbstring[0];
    var port = dbstring[1];
    crawlID = dbstring[2];
    console.log("Host:",host,"Port:",port,"CrawlID:",crawlID); 
} else {
    console.log("ERROR: database settings not found");
}

// Connect to database
socket.connect(host, port);

// Setup a dummy test table
var query = "CREATE TABLE IF NOT EXISTS ExtensionTest ( " +
            "   id INTEGER AUTOINCREMENT PRIMARY KEY, " +
            "   crawl_id INTEGER NOT NULL, " +
            "   url VARCHAR[500], " +
            "   title VARCHAR[500]);"
socket.send(query);

// Listen for new page loads and log page titles
var tabs = require("sdk/tabs");
tabs.on("ready", function(tab) {
    if (crawlID == null) {
        return;
    }
    var url = tab.url;
    var title = tab.title;
    console.log("URL:",url,"TITLE:",title);
    query = "INSERT INTO ExtensionTest crawl_id, url, title VALUES (?,?,?)";
    socket.send([query,[crawlID, url, title]]);
});
