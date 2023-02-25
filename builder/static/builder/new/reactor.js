function Event(name) {
  this.name = name;
  this.callbacks = [];
}

Event.prototype.registerCallback = function(callback) {
  this.callbacks.push(callback);
};

function Reactor() {
  this.events = {};
}

var reactorSingleton = (function(){
	var instance;
	return {
		getInstance: function() {
			if (!instance) {
				instance = new Reactor();
			}
			return instance;
		}
	};
})();

Reactor.prototype.registerEvent = function(eventName) {
  var event = new Event(eventName);
  this.events[eventName] = event;
};

Reactor.prototype.dispatchEvent = function(eventName, eventArgs) {
  this.events[eventName].callbacks.forEach(function(callback) {
    callback(eventArgs);
  });
};

Reactor.prototype.addEventListener = function(eventName, callback) {
  this.events[eventName].registerCallback(callback);
};
