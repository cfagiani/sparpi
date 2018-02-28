(function () { //scoping function

    var pollerInterval = null;

    /**
     * Cancels the pollerInterval if it is initialized.
     */
    function cancelPoll() {
        if (pollerInterval != null) {
            clearInterval(pollerInterval);
        }
    }

    /**
     * On page ready, bind the click listener to the button and a key listener to the input box.
     */
    $(document).ready(function () {
        $('#startbutton').click(function () {
            toggleWorkout();
        });

        $('#timeLeft').keyup(function () {
            validateInput();
        });

        $('.freq-ctl').keyup(function () {
            validateInput();
        });


        $('#recalibrate').click(function () {
            recalibrate();
        });
    });


    /**
     * Makes GET calls to the workout endpoint in order to load the current workout state. This will automatically
     * cancel the interval (if non-null) once the deadline has passed since no more updates should occur.
     */
    function pollForData() {
        $.getJSON("/workout",
            function (json) {
                updateWorkoutInfo(json);
                if (json['deadline'] - json['server_time'] <= 0) {
                    cancelPoll();
                    //turn the input fields back on
                    toggleAllowInput(true);
                }
            });
    }

    /**
     * Iterates the hitList array and returns a dictionary keyed on the hit direction.
     * @param hitList
     * @returns {{r: Array, c: Array, l: Array}}
     */
    function sortHits(hitList) {
        var hits = {
            r: [],
            c: [],
            l: []
        };
        for (var i = 0; i < hitList.length; i++) {
            hits[hitList[i]['direction']].push(hitList[i]);
        }
        return hits
    }

    /**
     * Updates the UI elements with data obtained from the current workoutState.
     * @param workoutState
     */
    function updateWorkoutInfo(workoutState) {
        $('#timeLeft').val(deadlineToTimeRemaining(workoutState['deadline'], workoutState['server_time']));
        var hits = sortHits(workoutState['correct_hits']);
        var misses = sortHits(workoutState['incorrect_hits']);
        $("#rhit").text(hits['r'].length);
        $("#chit").text(hits['c'].length);
        $("#lhit").text(hits['l'].length);
        $("#rtime").text(getAverage(hits['r']));
        $("#ctime").text(getAverage(hits['c']));
        $("#ltime").text(getAverage(hits['l']));
        $("#rmiss").text(misses['r'].length);
        $("#cmiss").text(misses['c'].length);
        $("#lmiss").text(misses['l'].length);
    }

    /**
     * Calculates the average reaction time from an array of hit information objects.
     * @param hits
     * @returns {*}
     */
    function getAverage(hits) {
        var total = 0;
        for (var i = 0; i < hits.length; i++) {
            total += hits[i]['time']
        }
        if (hits.length === 0) {
            return 0;
        } else {
            return (total / hits.length).toFixed(3);
        }
    }

    /**
     * Cancels the current workout.
     */
    function stopWorkout() {
        cancelPoll();
        $.ajax({
            url: '/workout',
            type: "POST",
            success: function () {
                toggleAllowInput(true);
            }
        });
    }


    function recalibrate() {
        $.ajax({
            url: '/calibration',
            type: "POST"
        });
    }

    /**
     *  Validates the time input box. Time input should be in the format SS  or MM:SS. Max time allowed is 99:99.
     * @returns {boolean}
     */
    function validateTime() {
        var isValid = /^([0-9]?[0-9])(:[0-9][0-9])?$/.test($("#timeLeft").val());
        if (isValid) {
            $("#timeForm").removeClass("text-danger");
            $("#timeLeft").removeClass("is-invalid");
        } else {
            $("#timeForm").addClass("text-danger");
            $("#timeLeft").addClass("is-invalid");
        }
        return isValid;
    }

    /**
     *  Validates the side frequency values. Frequencies should be an integer between 0 and 100 with a sum of
     * exactly 100.
     */
    function validateFrequencies() {
        //TODO: check this
        var freqElements = $(".freq-ctl");
        var total = 0
        for (var i = 0; i < freqElements.length; i++) {
            var element = freqElements.eq(i);
            var val = element.val();
            var isValid = /^([1]?[0-9]?[0-9])$/.test(val);
            if (isValid) {
                element.removeClass("text-danger");
            } else {
                element.addClass("text-danger");
                return false;
            }
            total += parseInt(val);
        }
        if (total != 100) {
            freqElements.addClass("text-danger");
            return false;
        }
        return true;
    }


    /**
     * Validates that we have a valid value in the timeLeft and frequency text input boxes.
     * @returns {boolean}
     */
    function validateInput() {
        var isValid = validateTime() && validateFrequencies();
        if (isValid) {
            $("#startbutton").removeClass("disabled");
        } else {
            $("#startbutton").addClass("disabled");
        }
        return isValid;
    }

    /**
     * Converts a string in the format mm:ss to fractional minutes.
     * @param timeString
     * @returns {number}
     */
    function timeStringToSeconds(timeString) {
        var parts = timeString.split(":");
        var minutes = 0;
        var seconds = 0;
        if (parts.length === 2) {
            minutes = parseInt(parts[0]);
            seconds = parseInt(parts[1]);
        } else {
            seconds = parseInt(parts[0]);
        }

        return (minutes * 60 + seconds) / 60;
    }


    /**
     * Takes a deadline and current server time (in seconds) and returns a string of the form "mm:ss" representing the
     * time until the deadline.
     * @param deadline
     * @param serverTime
     * @returns {string}
     */
    function deadlineToTimeRemaining(deadline, serverTime) {
        var totalSeconds = deadline - serverTime;
        var minutes = Math.max(Math.floor(totalSeconds / 60), 0);
        var secs = Math.max(Math.floor(totalSeconds % 60), 0);
        return minutes.toString() + ":" + secs.toString().padStart(2, '0');
    }

    /**
     * Initiates the workout on the server and kicks off a poll for workout information.
     */
    function startWorkout() {
        cancelPoll(); // just in case we were still polling for some reason
        if (validateInput()) {
            $.ajax({
                url: '/workout',
                type: "PUT",
                data: JSON.stringify({
                    time: timeStringToSeconds($("#timeLeft").val()),
                    mode: 'random',
                    frequencies: {
                        'r': parseInt($("#rFreq").val()),
                        'c': parseInt($("#cFreq").val()),
                        'l': parseInt($("#lFreq").val())
                    }
                }),
                dataType: "json",
                contentType: "application/json; charset=utf-8",
                success: function () {
                    //turn off input fields
                    toggleAllowInput(false);
                    pollerInterval = setInterval(pollForData, 500);
                }
            });
        }
    }

    /**
     * Starts or stops a workout based on the button press.
     */
    function toggleWorkout() {
        var buttonElement = $("#startbutton");
        if (buttonElement.text() === "Start") {
            buttonElement.text("Stop");
            startWorkout();
        } else {
            //disable since stopping may take a few seconds. the callback in stopWorkout should re-enable`
            buttonElement.addClass("disabled");
            stopWorkout();
            buttonElement.text("Start");
        }
    }

    /**
     * Enables or disables the text input fields.
     * @param isEnabled
     */
    function toggleAllowInput(isEnabled) {
        if (isEnabled) {
            $(".conf-ctl").removeClass("disabled");
            $(".conf-ctl:input").attr("disabled", false);
        } else {
            $(".conf-ctl").addClass("disabled");
            $(".conf-ctl:input").attr("disabled", true);
        }

    }
})();

