$(function() {
  console.log("We have liftoff");
  var button = new ButtonView({
    el: $('#realtime-button')
  });
});

var LogView = Backbone.View.extend({
  req: false,

  initialize: function() {
    // this.listenTo(this.model, 'change', this.render);
    this.model.on('change', this.render, this);
    this.intv = setInterval(function() {
      this.req = this.fetch();
    }.bind(this), 1000);
    this.req = this.fetch(true);
  },

  fetch: function(force) {
    if (force && this.req)
      this.req.abort();
    else if (this.req.readyState != 4)
      return;

    this.req = this.model.fetch();
  },

  render: function() {
    this.$el.empty();
    var data = this.model.get('logs');
    data.forEach(function(item) {
      this.renderLine(item);
    }.bind(this));
  },

  renderLine: function(line) {
    if (line.startsWith('!IMAGE')) {
      line = line.slice(7, line.length-1);
      var el = $('<img src="data:image/jpg;base64,' + line + '">');
      this.$el.append(el);
    } else {
      this.$el.append(line + '\n');
    }
  }
});

var Log = Backbone.Model.extend({
  urlRoot: '/logdata',

  parse: function(response, options) {
    console.log(response);
    return response;
  }
});

var ButtonView = Backbone.View.extend({
  enabled: false,

  events: {
    'click':  'enable'
  },

  enable: function() {
    if (this.enabled)
      return;

    var log = new Log({
      id: window.LogID
    });

    new LogView({
      model: log,
      el: $('#logs')
    });

    this.$el.addClass('disabled btn-success');
    this.$el.removeClass('btn-primary');
    this.enabled = true;
  }
});
