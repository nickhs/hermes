var express = require('express');
var uuid = require('node-uuid');
var app = module.exports = express.createServer();
var fs = require('fs');

TIMEOUT = 180000
captchas = []

var allowCrossDomain = function(req, res, next) {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST');
  res.header('Access-Control-Allow-Headers', 'Content-Type');

  next();
}

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

app.post('/captcha', function(req, res) {
  console.log("Received data!");

  var id = uuid.v4();
  image = new Buffer(req.body.image, 'base64');
  fs.writeFile(__dirname+'/captchas/'+id+'.png', image, function(err) {});

  var temp = {
    id: id,
    time: new Date(),
    file: '/captchas/'+id+'.png',
    solved: false,
  };

  captchas.push(temp);
  console.log(temp);

  var intv = setInterval(function() {
    for (var i=0; i < captchas.length; i++) {
      if (captchas[i].id == id) {
        if (captchas[i].solved != false) {
          console.log("Solved! "+captchas[i].id);
          res.send(captchas[i].solved);
          fs.unlink(__dirname+captchas[i].file);
          captchas.splice(i, 1);
          clearInterval(intv);
        }

        else if ((captchas[i].time.getTime() + TIMEOUT) < (new Date().getTime())) {
          console.log("Captcha operation timed out :( ");
          res.send('failed');
          captchas.splice(i, 1);
          clearInterval(intv);
        }
        break;
      }
    }
  }, 2000);
});


app.get('/', function(req, res) {
  console.log("Fooo");
  var r = null;

  if (captchas.length > 0) {
    for (var i=0; i < captchas.length; i++) {
      if (captchas[i].solved == false) {
        r = captchas[i];
        break;
      }
    }
  }

  if (r == null) {
    res.send('Got nothing for you :(');
  }

  else {
    res.render('main', {'captcha': r});
  }
});

app.post('/', function(req, res) {
  console.log("I got posted!");
  for (var i=0; i < captchas.length; i++) {
    if (req.body.id == captchas[i].id) {
      console.log("Match found!");
      captchas[i].solved = req.body.answer;
      break;
    }
  }
  console.log(captchas);
  res.redirect('/');
});

app.listen(8060, function() {
  console.log("Listening...");
});
