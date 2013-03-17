var express = require('express');
var uuid = require('node-uuid');
var app = module.exports = express.createServer();
var fs = require('fs');
var WebSocketServer = require('ws').Server;
var wss = new WebSocketServer({port: 8080});

var TIMEOUT = 1800000;
var captchas = [];

var allowCrossDomain = function(req, res, next) {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST');
  res.header('Access-Control-Allow-Headers', 'Content-Type');

  next();
};

app.configure(function() {
  app.set('views', __dirname + '/views');
  app.set('view engine', 'jade');
  app.set('view options', { layout: false });
  app.use(express.bodyParser());
  app.use(allowCrossDomain);
  app.use(express.errorHandler({ dumpExceptions: true, showStack: true }));
  app.use('/captchas', express.static(__dirname+'/captchas'));
  app.use(express.static(__dirname + '/static'));
});

wss.on('connection', function(ws) {
  ws.on('message', function(msg) {
    console.log('Received data!');

    var id = uuid.v4();
    var image = new Buffer(msg, 'base64');
    fs.writeFile(__dirname+'/captchas/'+id+'.png', image, null);

    var temp = {
      id: id,
      time: new Date(),
      file: '/captchas/'+id+'.png',
      solved: false
    };

    console.log(temp);
    temp.ws = ws;
    captchas.push(temp);

    var intv = setInterval(function() {
      for (var i=0; i < captchas.length; i++) {
        var captcha = captchas[i];

        if (captcha.id == id) {
          if (captcha.solved !== false) {
            console.log('Solved! '+captcha.id);
            ws.send(captcha.solved);
            fs.unlink(__dirname+captcha.file);
            captchas.splice(i, 1);
            clearInterval(intv);
          }

          else if ((captcha.time.getTime() + TIMEOUT) < (new Date().getTime())) {
            console.log('Captcha operation timed out :( ');

            try {
              ws.send('failed');
            } catch (err) {
              console.log(err);
              console.log('Client probably ditched me. Bastard');
            }

            captchas.splice(i, 1);
            clearInterval(intv);
          }
          break;
        }
      }
    }, 2000);
  });
});


app.get('/', function(req, res) {
  console.log('Fooo');
  var r = null;

  if (captchas.length > 0) {
    for (var i=0; i < captchas.length; i++) {
      if (captchas[i].solved === false) {
        r = captchas[i];
        break;
      }
    }
  }

  if (r === null) {
    res.send('Got nothing for you :(');
  }

  else {
    res.render('main', {'captcha': r});
  }
});

app.post('/', function(req, res) {
  console.log('I got posted!');
  for (var i=0; i < captchas.length; i++) {
    if (req.body.id == captchas[i].id) {
      console.log('Match found!');
      captchas[i].solved = req.body.answer;
      break;
    }
  }
  console.log(captchas);
  res.redirect('/');
});

app.listen(8060, function() {
  console.log('Listening...');
});
