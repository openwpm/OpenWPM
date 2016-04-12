// FlashCookie.js v0.0.1
// JavaScript interface library to manage persistent cross-browser Flash cookies.
// https://github.com/faisalman/flash-cookie-js
//
// Copyright © 2013 Faisalman <fyzlman@gmail.com>
// Dual licensed under GPLv2 & MIT

;(function (window) {
    'use strict';
    var movieName = 'FlashCookie';
    var movieURL = 'FlashCookie.swf';
    var ready = new CustomEvent('ready', {});
    var object = document.createElement('object');
    var param1 = document.createElement('param');
    var param2 = document.createElement('param');
    var embed = document.createElement('embed');
    object.id = movieName;
    object.width = '600';
    object.height = '400';
    object.style.position = 'absolute';
    object.style.top = '-9999px';
    object.style.left = '-9999px';
    param1.name = movieName;
    param1.value = movieURL;
    object.appendChild(param1);
    param2.name = 'allowScriptAccess';
    param2.value = 'sameDomain';
    object.appendChild(param2);
    embed.name = movieName;
    embed.src = movieURL;
    embed.width = '600';
    embed.height = '400';
    embed.allowscriptaccess = 'sameDomain';
    object.appendChild(embed);
    document.body.appendChild(object);
    window.FlashCookie = {};
    window.FlashCookie.onReady = function (callback) {
        document.body.addEventListener('ready', function () {
            callback.call(this, document[movieName]);
        });
    };
    window.FlashCookie.showConsole = function () {
        var object = document.getElementById(movieName);
        object.style.top = 0;
        object.style.left = 0;
    };
    document.body.onload = function () {
        setTimeout(function () {
            document.body.dispatchEvent(ready);
        }, 200);
    };
})(this);