var casper = require('casper').create({
  verbose: true,
  logLevel: 'debug',
  pageSettings: {
    javascriptEnabled: true,
    loadImages: true,
    loadPlugins: true,
    localToRemoteUrlAccessEnabled: true,
    userAgent: "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
    webSecurity: false,
  },
  safeLogs: false,
  viewportSize: {
    height: 800,
    width: 1280,
  },
});

function handleImage(data) {
  var fd = new FormData();
  fd.append('image', data);

  if (!casper.cli.has('host')) {
    casper.die("No host defined!", 1);
  }

  var host = casper.cli.get('host');
  casper.log("HOST IS " + host);

  var req = new XMLHttpRequest();
  req.open("POST", host, false);
  req.timeout = 180000;
  req.addEventListener("error", failedCaptcha);
  req.addEventListener('load', gotCaptcha);

  try {
    req.send(fd)
  } catch(err) {
    casper.log(JSON.stringify(err))
  }
}

function failedCaptcha(err) {
  casper.log(JSON.stringify(err));
  casper.log(JSON.stringify(this));
  casper.die("Failed to get captcha!", 1);
}

function gotCaptcha(resp) {
  console.log(JSON.stringify(resp));
  casper.log("Got resp!");
  casper.log(casper.getTitle());

  casper.fill('form#login_reg', {
    'user': casper.cli.get('username'),
    'passwd': casper.cli.get('password'),
    'passwd2': casper.cli.get('password'),
    'captcha': resp.target.response,
  });

  casper.wait(6000, function() {
    casper.thenClick('#login_reg button');
  });
}

casper.start('http://www.reddit.com/', function() {
  if (!this.cli.has('username')) {
    casper.die("You need to specify a username!", 1);
  }
  this.click("#header-bottom-right > span > a");
});

casper.wait(15000, function() {
  var data = this.captureBase64('png', '.capimage');
  handleImage(data);
});

casper.then(function() {
  casper.wait(90000, function() {
    if (casper.visible('.popup')) {
      casper.log('Abort. Popup still exists', 'error')
      abort();
    } else {
      if (casper.cli.get('username') == casper.fetchText('span.user a')) {
        casper.log('Run complete. User created', 'info')
        casper.log('Username: ' + casper.cli.get('username'), 'info')
        casper.log('Password: ' + casper.cli.get('password'), 'info')
        casper.exit(0)
      } else {
        casper.log('Unknown error', 'error');
        abort();
      }
    }
  });
});

function abort() {
  screenshot('error.png')
  casper.die('Fatal Error. Exiting', 1);
}

function screenshot(name) {
  if (casper.cli.get('headless'))
    casper.echo('!IMAGE:' + casper.captureBase64('jpg', 'body'));
  else
    casper.capture(name)
}


casper.run(function() {
  casper.log("Halted exit");
});
