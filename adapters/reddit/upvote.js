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
  }
});

var dump = require('utils').dump;


function getUrl() {
  var base  = "http://reddit.com/";

  if (casper.cli.has('subreddit')) {
    return base + "r/" + casper.cli.get('subreddit');
  }

  casper.log("getURL called")
  return base;
}

casper.start(getUrl(), function() {
  if (!(this.cli.has('username') && this.cli.has('password'))) {
    casper.die("You need to specify a username and password!", 1);
  }

  this.click("#header-bottom-right > span > a");
});

casper.then(function() {
  this.fill('form#login_login', {
    'user': this.cli.get('username'),
    'passwd': this.cli.get('password')
  }, true);
});

casper.then(function() {
  this.wait(3000)
});

casper.thenOpen(getUrl());

casper.then(function() {
  var ret = casper.evaluate(function() {
    document.body.bgColor = 'white';
    var titles = []
    var links = document.querySelectorAll('#siteTable .thing.link');
    for (var i = 0; i < links.length; ++i) {
      var item = {};
      item.title = links[i].querySelector('a.title').textContent;
      item.url = links[i].querySelector('a.title').href;

      var uparrow = links[i].querySelector('div.arrow.up')
      if (uparrow === null) {
        item.upvoted = true;
      } else {
        uparrow.className += ' foo-'+i;
      }

      titles.push(item);
    }
    return titles;
  });

  screenshot('before.jpg')
  if (!ret || ret.length == 0) {
    casper.log(JSON.stringify(ret), 'warning');
    casper.log('No links found!', 'error');
    abort();
  }

  for (var i = 0; i < ret.length; ++i) {
    var item = ret[i];

    if (item.upvoted)
      continue;

    if (item.title === this.cli.get('post')) {
      this.log('Match found!', 'info');
      this.log(item.title);
      this.log(item.url);
      performClick(i);
    } else if (Math.random() * i <= 0.5) {
      this.log('Random selection', 'info');
      this.log(item.title, 'info');
      this.log(item.url, 'info');
      performClick(i);
    }
  }

});

casper.then(function() {
  screenshot("finish.jpg");
});

function performClick(i) {
  casper.wait(5000 + Math.floor(Math.random() * 10000), function() {
    casper.mouseEvent('mouseover', 'div.foo-'+i);
    casper.mouseEvent('mousedown', 'div.foo-'+i);
    casper.mouseEvent('click', 'div.foo-'+i);
    casper.mouseEvent('mouseup', 'div.foo-'+i);
    casper.mouseEvent('mouseout', 'div.foo-'+i);
  });
}

function abort() {
  screenshot('error.jpg')
  casper.die('Fatal Error. Exiting', 1);
}

function screenshot(name) {
  if (casper.cli.get('headless'))
    casper.echo('!IMAGE:' + casper.captureBase64('jpg', 'body'));
  else
    casper.capture(name)
}

casper.on('error', function(err) {
  casper.log(JSON.stringify(err), 'error');
  abort();
});

casper.on('page.error', function(err) {
  casper.log(JSON.stringify(err), 'error');
  abort();
});

casper.run();
