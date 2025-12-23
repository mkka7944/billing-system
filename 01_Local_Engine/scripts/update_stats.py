import re

# Read the original file
with open('g:/Other computers/My Computer/qoder/billing-system/01_Local_Engine/scripts/final-cp.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the new showSurveyorStats function
new_function = '''        function showSurveyorStats() {
            var modal = document.getElementById('statsModal');
            var container = document.getElementById('statsContent');
            
            if (currentFilteredSurveys.length === 0) {
                alert("No data found for current filters. Please apply filters first.");
                return;
            }

            // Helper function to parse datetime
            function parseDateTime(dateStr, timeStr) {
                if (!dateStr || !timeStr) return null;
                
                // Handle various date formats
                var dateParts = dateStr.split('-');
                if (dateParts.length !== 3) return null;
                
                // Handle various time formats
                var timeParts = timeStr.split(':');
                if (timeParts.length < 2) return null;
                
                var year = parseInt(dateParts[0]);
                var month = parseInt(dateParts[1]) - 1; // JS months are 0-indexed
                var day = parseInt(dateParts[2]);
                var hour = parseInt(timeParts[0]) || 0;
                var minute = parseInt(timeParts[1]) || 0;
                var second = parseInt(timeParts[2]) || 0;
                
                return new Date(year, month, day, hour, minute, second);
            }

            // Helper function to format time for display
            function formatTime(dateObj) {
                if (!dateObj) return 'N/A';
                return dateObj.toLocaleTimeString('en-US', {hour12: false, hour: '2-digit', minute:'2-digit'});
            }

            // Helper function to format date for display
            function formatDate(dateObj) {
                if (!dateObj) return 'N/A';
                return dateObj.toLocaleDateString('en-GB'); // DD/MM/YYYY format
            }

            // Helper function to check if time is within lunch hours (1pm-2pm)
            function isLunchHour(dateTime) {
                if (!dateTime) return false;
                var hour = dateTime.getHours();
                return hour >= 13 && hour < 14; // 1pm to 2pm
            }

            // Helper function to check if time is within PM hours (2pm-5pm)
            function isPMHours(dateTime) {
                if (!dateTime) return false;
                var hour = dateTime.getHours();
                return hour >= 14 && hour < 17; // 2pm to 5pm
            }

            // Aggregate data with enhanced stats
            var stats = {};
            currentFilteredSurveys.forEach(function(survey) {
                var name = survey.surveyor_name || "Unknown Surveyor";
                var surveyDateTime = parseDateTime(survey.survey_date, survey.survey_time);
                
                if (!stats[name]) {
                    stats[name] = { 
                        total: 0, 
                        domestic: 0, 
                        commercial: 0,
                        firstSubmission: surveyDateTime,
                        lastSubmission: surveyDateTime,
                        submissions: [] // Store all submissions for idle time calculation
                    };
                } else {
                    // Update first and last submission times
                    if (surveyDateTime && (!stats[name].firstSubmission || surveyDateTime < stats[name].firstSubmission)) {
                        stats[name].firstSubmission = surveyDateTime;
                    }
                    if (surveyDateTime && (!stats[name].lastSubmission || surveyDateTime > stats[name].lastSubmission)) {
                        stats[name].lastSubmission = surveyDateTime;
                    }
                }
                
                stats[name].total++;
                if (survey.consumer_type === 'Domestic') stats[name].domestic++;
                if (survey.consumer_type === 'Commercial') stats[name].commercial++;
                
                // Store submission for idle time calculation
                if (surveyDateTime) {
                    stats[name].submissions.push({
                        dateTime: surveyDateTime,
                        time: survey.survey_time
                    });
                }
            });

            // Calculate idle times and PM performance
            Object.keys(stats).forEach(function(name) {
                var stat = stats[name];
                
                // Sort submissions by time
                stat.submissions.sort(function(a, b) {
                    return a.dateTime - b.dateTime;
                });
                
                // Calculate idle time
                stat.idleMinutes = 0;
                stat.idleWarning = '';
                
                if (stat.submissions.length > 1) {
                    var maxIdleMinutes = 0;
                    
                    for (var i = 1; i < stat.submissions.length; i++) {
                        var prevTime = stat.submissions[i-1].dateTime;
                        var currTime = stat.submissions[i].dateTime;
                        
                        // Skip lunch hour (1pm-2pm) for idle time calculation
                        if (isLunchHour(prevTime) || isLunchHour(currTime)) {
                            continue;
                        }
                        
                        var idleMs = currTime - prevTime;
                        var idleMin = Math.floor(idleMs / (1000 * 60));
                        
                        if (idleMin > maxIdleMinutes) {
                            maxIdleMinutes = idleMin;
                        }
                    }
                    
                    stat.idleMinutes = maxIdleMinutes;
                    
                    // Set warning based on idle time
                    if (maxIdleMinutes >= 60) {
                        stat.idleWarning = 'ABSENT (60+ min idle)';
                    } else if (maxIdleMinutes >= 30) {
                        stat.idleWarning = 'WARNING (30+ min idle)';
                    }
                }
                
                // Calculate PM performance (2pm-5pm)
                stat.pmCount = 0;
                stat.pmPerformance = '';
                
                stat.submissions.forEach(function(submission) {
                    if (isPMHours(submission.dateTime)) {
                        stat.pmCount++;
                    }
                });
                
                // Mark as absent if PM count is less than 40
                if (stat.pmCount < 40 && stat.pmCount > 0) {
                    stat.pmPerformance = 'ABSENT (less than 40 submissions)';
                } else if (stat.pmCount === 0) {
                    stat.pmPerformance = 'NO PM ACTIVITY';
                }
            });

            // Sort surveyors by total count descending
            var sortedNames = Object.keys(stats).sort(function(a, b) {
                return stats[b].total - stats[a].total;
            });

            // Generate Table
            var html = '<table class="stats-table">' +
                       '<thead><tr>' +
                       '<th>#</th><th>Surveyor Name</th><th>First Submission</th><th>Last Submission</th><th>Domestic</th><th>Commercial</th><th>Total Submissions</th><th>Idle Minutes</th><th>Idle Status</th><th>PM Count</th><th>PM Performance</th>' +
                       '</tr></thead><tbody>';

            sortedNames.forEach(function(name, index) {
                var s = stats[name];
                html += '<tr>' +
                        '<td><span class="rank-badge">' + (index + 1) + '</span></td>' +
                        '<td style="font-weight:bold; color:#2c3e50;">' + name + '</td>' +
                        '<td>' + (s.firstSubmission ? formatDate(s.firstSubmission) + ' ' + formatTime(s.firstSubmission) : 'N/A') + '</td>' +
                        '<td>' + (s.lastSubmission ? formatDate(s.lastSubmission) + ' ' + formatTime(s.lastSubmission) : 'N/A') + '</td>' +
                        '<td style="color:#27ae60;">' + s.domestic + '</td>' +
                        '<td style="color:#e67e22;">' + s.commercial + '</td>' +
                        '<td style="font-weight:bold;">' + s.total + '</td>' +
                        '<td>' + s.idleMinutes + '</td>' +
                        '<td style="font-weight:' + (s.idleWarning ? 'bold' : 'normal') + '; color:' + (s.idleWarning.includes('ABSENT') ? '#e74c3c' : s.idleWarning.includes('WARNING') ? '#f39c12' : '#2c3e50') + ';">' + (s.idleWarning || 'OK') + '</td>' +
                        '<td>' + s.pmCount + '</td>' +
                        '<td style="font-weight:' + (s.pmPerformance ? 'bold' : 'normal') + '; color:' + (s.pmPerformance.includes('ABSENT') ? '#e74c3c' : s.pmPerformance ? '#f39c12' : '#2c3e50') + ';">' + (s.pmPerformance || 'ACTIVE') + '</td>' +
                        '</tr>';
            });

            html += '</tbody></table>';
            
            // Add a grand total footer
            html += '<div style="margin-top:20px; padding:15px; background:#f8f9fa; border-radius:8px; border-left:4px solid #9b59b6;">' +
                    '<strong>Total Records in Selection:</strong> ' + currentFilteredSurveys.length + '</div>';

            container.innerHTML = html;
            modal.style.display = 'block';
        }'''

# Replace the old function with the new one
pattern = r'function showSurveyorStats\(\).*?function closeStatsView\(\)'
replacement = new_function + '\n\n        function closeStatsView()'
updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write the updated content back to the file
with open('g:/Other computers/My Computer/qoder/billing-system/01_Local_Engine/scripts/final-cp.py', 'w', encoding='utf-8') as f:
    f.write(updated_content)

print("Successfully updated the showSurveyorStats function!")