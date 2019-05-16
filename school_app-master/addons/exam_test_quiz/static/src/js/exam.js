odoo.define('exam_test_quiz.exam', function(require) {
    'use strict';

    var website = require('website.website');
    // var session = require('web.session');
    // var ajax = require('web.ajax');
    /*
     * This file is intended to add interactivity to survey forms rendered by
     * the website engine.
     */

    var the_form = $('.js_examform');

    if (!the_form.length) {
        return $.Deferred().reject("DOM doesn't contain '.js_examform'");
    }

    console.debug("Custom JS for Exam is loading...");
    var starttime = the_form.attr("data-starttime");
    var endtime = the_form.attr("data-endtime");
    //window.open("http://www.google.com","PopupWindow", "toolbar=no,menubar=no"); 

    // window.addEventListener('blur', function(){
    //     console.log('blur');
    //     }, false);

    // window.addEventListener('focus', function(){
    //     console.log('focus');
    //     }, false);
    var startdate = new Date(starttime);
    var today = new Date()

    var countDownDate = new Date(endtime).getTime();
    var count = 0;

    // if (today.getDate() != startdate.getDate() || today.getFullYear() != startdate.getFullYear() 
    //     && today.getMonth() != startdate.getMonth()){
    if (today.toLocaleDateString() != startdate.toLocaleDateString()) {

        alert("Exam Date Is Not Today");
        document.getElementById("finish").disabled = true;
        $.ajax('/web', {'redirect': '/web'});
    }


    // Update the count down every 1 second
    var x = setInterval(function() {

        // Get todays date and time
        var now = new Date().getTime();
        count = count + 1;

        // Find the distance between now and the count down date
        var distance = countDownDate - now;

        // Time calculations for days, hours, minutes and seconds
        var days = Math.floor(distance / (1000 * 60 * 60 * 24));
        var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        var seconds = Math.floor((distance % (1000 * 60)) / 1000);
        document.getElementById("demo").innerHTML = hours + "h " +
            minutes + "m " + seconds + "s ";
        if (distance < 0 && count === 1) {
            clearInterval(x);
            document.getElementById("demo").innerHTML = "EXPIRED";

            document.getElementById("finish").disabled = true;
            // $("#finish").off("click");
            // $.ajax("/web/session/logout").then(function(results) {
            //     console.log('Logout Successful')

            //     $.ajax('/web/login', {
            //         redirect: '/web'
            //     }).then(function(action) {
            //         console.log('Login Page')
            //     }, function() {});

            // });
        }
        if (distance < 0 && count > 1) {
            clearInterval(x);
            document.getElementById("demo").innerHTML = "EXPIRED";
            $("#finish").click()
            document.getElementById("finish").disabled = true;
            // $("#finish").off("click");
            // $.ajax("/web/session/logout").then(function(results) {
            //     console.log('Logout Successful')

            //     $.ajax('/web/login', {
            //         redirect: '/web'
            //     }).then(function(action) {
            //         console.log('Login Page')
            //     }, function() {});

            // });
        }
    }, 1000);


    $(document).ready(function() {


        $("body").on("contextmenu", function(e) { // Disable Right Click
            return false;
        });
        document.onkeydown = function(e) {
            if (e.keyCode === 123) { // disable F12
                return false;
            }


            $('body').bind('cut copy paste', function(e) {
                e.preventDefault();
            });


            if (e.ctrlKey && e.keyCode == 83) { // disable Ctrl+S
                return false;
            }

            if (e.ctrlKey && (e.keyCode === 85)) { // disable Ctrl+U
                return false;
            }

            if (e.ctrlKey && e.shiftKey && e.keyCode == 73) { // disable Ctrl+Shift+I
                return false;
            }

            if (e.ctrlKey && e.shiftKey && e.keyCode == 67) { // disable Ctrl+Shift+C
                return false;
            }
        };



    })



});
