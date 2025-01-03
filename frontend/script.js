document.addEventListener('DOMContentLoaded', function() {
    const username = localStorage.getItem('username');
    const fullName = localStorage.getItem('fullName');
    const role = localStorage.getItem('role');
    const activeModel = localStorage.getItem('activeModel') || 'Naive Bayes';
    
    if (username) {
        document.getElementById('username-display').textContent = fullName + " (" + role + ")";
    } else {
        window.location.href = 'login.html'; // Redirect to login if no user is found
    }

    // Fetch current model
    function fetchCurrentModel() {
        fetch('http://127.0.0.1:5002/api/model/current')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                console.log('Current model:', data.current_model);
                const currentModel = data.current_model;
                localStorage.setItem('activeModel', currentModel);

                // Set active model button
                const activeButton = document.getElementById(currentModel.toLowerCase().replace(/ /g, '-'));
                if (activeButton) {
                    activeButton.classList.add('active');
                    activeButton.style.backgroundColor = '#e9970b';
                }
            })
            .catch(error => {
                console.error('Error fetching current model:', error);
                // Handle error without showing notification
            });
    }

    fetchCurrentModel();

    // Function to select model
    window.selectModel = function(model) {
        localStorage.setItem('activeModel', model);
        document.querySelectorAll('.model-buttons button').forEach(button => {
            button.classList.remove('active');
            button.style.backgroundColor = ''; // Reset background color
        });
        const selectedButton = document.getElementById(model.toLowerCase().replace(/ /g, '-'));
        if (selectedButton) {
            selectedButton.classList.add('active');
            selectedButton.style.backgroundColor = '#e9970b';
        }

        // Send API request to activate model
        fetch('http://127.0.0.1:5002/api/model/setup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model_name: model
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            console.log('API response (setup model):', data);
            // Display notification or perform other actions based on API response
            alert(data.message);
        })
        .catch(error => {
            console.error('Error setting up model:', error);
        });

        // Add logic here to switch model for predictions
        console.log('Selected model:', model); // For debugging
    };
    
    // Logout function
    window.logout = function() {
        localStorage.removeItem('username');
        window.location.href = 'login.html';
    };

    const totalEmailsUrl = 'http://127.0.0.1:5002/api/emails/count';
    const newestEmailsUrl = 'http://127.0.0.1:5002/api/emails/ordered-by-received-datetime';

    // Fetch and update total emails and details immediately when the page is loaded
    fetchAndUpdateTotalEmails();
    fetchDetailEmails();

    // Fetch and update total emails and details every 5 seconds
    setInterval(fetchAndUpdateTotalEmails, 5000);
    setInterval(fetchDetailEmails, 5000);

    // Fetch total emails
    function fetchAndUpdateTotalEmails() {
        fetch(totalEmailsUrl)
            .then(response => response.json())
            .then(data => {
                console.log('API response:', data); // Check API response
                document.getElementById('recipients').innerText = data.total_emails;
                document.getElementById('total-phishing').innerText = data.total_phishing_emails;
                document.getElementById('unclassified').innerText = data.total_unlabeling_emails_by_user;
                document.getElementById('report-by-users').innerText = data.total_emails_report_by_user;
                
            })
            .catch(error => console.error('Error fetching total emails:', error));
    }

    // Search function
    window.searchTable = function() {
        const input = document.getElementById('searchBox');
        const filter = input.value.toUpperCase();
        const table = document.querySelector('.table-container table');
        const tr = table.getElementsByTagName('tr');

        for (let i = 1; i < tr.length; i++) {
            let display = false;
            const tds = tr[i].getElementsByTagName('td');
            for (let j = 0; j < tds.length; j++) {
                const td = tds[j];
                if (td) {
                    const txtValue = td.textContent || td.innerText;
                    if (txtValue.toUpperCase().indexOf(filter) > -1) {
                        display = true;
                        break;
                    }
                }
            }
            tr[i].style.display = display ? '' : 'none';
        }
    };
    
    // Fetch 20 newest emails
    function fetchDetailEmails() {
        fetch(newestEmailsUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                const emailTableBody = document.getElementById('newest-emails');
                emailTableBody.innerHTML = '';
                data.emails.forEach((email, index) => {
                    const classificationColor = email.classification.toLowerCase() === 'phishing' ? '#ff0000' : '#008000'; // Red for phishing, green for legit
                    const classificationofUserColor = email.classificationOfUser.trim() === '' 
                        ? '' 
                        : email.classificationOfUser.toLowerCase() === 'phishing' 
                            ? '#ff0000' 
                            : '#008000';
                    const buttonColor = '#e9970b';
                    const row = `<tr>
                                    <td>
                                        <a href="#" onclick="fetchEmailDetails('${email.mailId}'); return false;">
                                            ${email.mailId}
                                        </a>
                                    </td>
                                    <td><button id="toggleButton-${index}" style="background-color: ${buttonColor}; color: white; width: 100%;" onclick="window.toggleClassification(${index}, '${email.mailId}', '${email.classification}')">Revert</button></td>
                                    <td style="background-color: ${classificationColor};">${email.classification}</td>
                                    <td>${email.classifyBy}</td>
                                    <td>${email.receivedDateTime}</td>
                                    <td>${email.classifyByUser}</td>
                                    <td style="background-color: ${classificationofUserColor};">${email.classificationOfUser}</td>
                                    <td>${email.fromEmailAddress}</td>
                                    <td>${email.toRecipientEmailAddress}</td>
                                    <td>${email.subject}</td>
                                    <td>${email.bodyPreview}</td>
                                    <td>${email.isRead}</td>
                                    <td>${email.lastModifiedDateTime}</td>
                                </tr>`;
                    emailTableBody.insertAdjacentHTML('beforeend', row);
                });
            })        
            .catch(error => console.error('Error fetching newest emails:', error));
    }

    // Fetch email details and display in a new window
    window.fetchEmailDetails = function(emailId) {
        fetch('http://127.0.0.1:5002/api/email/' + emailId)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                console.log('Email details:', data);
                openEmailDetailWindow(data);
            })
            .catch(error => console.error('Error fetching email details:', error));
    }

    // Open a new window and display email details
    function openEmailDetailWindow(email) {
        const emailDetailWindow = window.open("", "_blank", "width=600,height=400");
        emailDetailWindow.document.write(`
            <html>
                <head>
                    <title>Email Details</title>
                    <style>
                        body { font-family: Arial, sans-serif; padding: 20px; }
                        h3 { margin-top: 0; }
                        p { margin: 5px 0; }
                        .email-content { border-top: 1px solid #ccc; margin-top: 20px; padding-top: 20px; }
                    </style>
                </head>
                <body>
                    <h3>${email.mailId}</h3>
                    <h3>${email.subject}</h3>
                    <p><strong>From:</strong> ${email.senderName} (${email.senderEmailAddress})</p>
                    <p><strong>To:</strong> ${email.toRecipientName} (${email.toRecipientEmailAddress})</p>
                    <p><strong>Received:</strong> ${email.receivedDateTime}</p>
                    <p><strong>Classification:</strong> ${email.classification}</p>
                    <div class="email-content">${email.bodyContent}</div>
                    <button onclick="window.close()">Close</button>
                </body>
            </html>
        `);
    }

    // Toggle classification
    window.toggleClassification = function(index, emailId, currentClassification,) {
        if (confirm("Are you sure you want to revert the classification?")) {
            const emailClassificationElement = document.getElementById(`classification-${index}`);
            const emailClassifyByElement = document.getElementById(`classifyBy-${index}`);
            const toggleButton = document.getElementById(`toggleButton-${index}`);

            const newClassification = currentClassification === 'Phishing' ? 'Legit' : 'Phishing';
            //const newClassificationColor = newClassification === 'Phishing' ? '#ff0000' : '#008000';
            
            // Send API request to update classification
            fetch('http://127.0.0.1:5002/api/classify_email', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email_id: emailId,
                    classification: newClassification,
                    classify_by_user: fullName
                    
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                console.log('API response (update classification):', data);

                // Update UI
                //emailClassificationElement.textContent = newClassification;
                //emailClassificationElement.style.backgroundColor = newClassificationColor;
                //toggleButton.textContent = 'Revert';
                //toggleButton.style.backgroundColor = '#e9970b';
                //emailClassifyByElement.textContent = fullName;
            })
            .catch(error => console.error('Error updating email classification:', error));
        }
    };

    // Fetch data and generate charts
    generateCharts();

    function generateCharts() {

        // Total and Phishing Emails Over Time (Line Chart)
        function fetchEmailStatistics() {
            fetch('http://127.0.0.1:5002/api/emails/total-by-date')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                console.log('API response:', data);
    
                // Get data from API
                const labels = data.total_emails_by_date.map(entry => entry.date);
                const totalEmailsData = data.total_emails_by_date.map(entry => entry.total);
                const phishingEmailsData = data.total_phishing_emails_by_date.map(entry => entry.total);
    
                // Update chart
                phishingTrendChart.data.labels = labels;
                phishingTrendChart.data.datasets[0].data = totalEmailsData;
                phishingTrendChart.data.datasets[1].data = phishingEmailsData;
                phishingTrendChart.update();
            })
            .catch(error => {
                console.error('Error fetching email statistics:', error);
            });
        }
    
        // Chart with dynamic data from API
        const phishingTrendCtx = document.getElementById('phishingTrendChart').getContext('2d');
        const phishingTrendChart = new Chart(phishingTrendCtx, {
            type: 'line',
            data: {
                labels: [], // To be updated dynamically from API
                datasets: [
                    {
                        label: 'Total Receipts',
                        data: [], // To be updated dynamically from API
                        borderColor: 'rgba(255, 99, 132, 1)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        fill: false
                    },
                    {
                        label: 'Phishing Emails',
                        data: [], // To be updated dynamically from API
                        borderColor: 'rgba(75, 192, 192, 1)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        beginAtZero: true
                    },
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    
        // Call fetchEmailStatistics when page is loaded
        fetchEmailStatistics();
    
        // Set up data refresh every 3 seconds
        setInterval(fetchEmailStatistics, 5000);

        // Open and Report Phishing Emails Over Time (Line Chart)
        function PhisingOpenAndReportByUser() {
            fetch('http://127.0.0.1:5002/api/emails/phishing-by-date')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                console.log('API response:', data);
    
                // Get data from API
                const labels = data.total_phishing_email_opens_by_date.map(entry => entry.date);
                const phishingOpensData = data.total_phishing_email_opens_by_date.map(entry => entry.total);
                const reportedEmailsData = data.total_reported_emails_by_date.map(entry => entry.total);
    
                // Update chart
                phishingOpensReportsChart.data.labels = labels;
                phishingOpensReportsChart.data.datasets[0].data = phishingOpensData;
                phishingOpensReportsChart.data.datasets[1].data = reportedEmailsData;
                phishingOpensReportsChart.update();
            })
            .catch(error => {
                console.error('Error fetching phishing email statistics:', error);
            });
        }
    
        // Chart with dynamic data from API
        const phishingOpensReportsCtx = document.getElementById('phishingOpensReportsChart').getContext('2d');
        const phishingOpensReportsChart = new Chart(phishingOpensReportsCtx, {
            type: 'bar',
            data: {
                labels: [], // To be updated dynamically from API
                datasets: [
                    {
                        label: 'Opened',
                        data: [], // To be updated dynamically from API
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Reported',
                        data: [], // To be updated dynamically from API
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    x: {
                        beginAtZero: true
                    },
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    
        // Call PhisingOpenAndReportByUser when page is loaded
        PhisingOpenAndReportByUser();
    
        // Set up data refresh every 3 seconds
        setInterval(PhisingOpenAndReportByUser, 5000);

        // Phishing Emails by Model (Doughnut Chart)
        function fetchPhishingEmailByModel() {
            fetch('http://127.0.0.1:5002/api/emails/count-by-model')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok ' + response.statusText);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('API response:', data);
    
                    // Get data from API
                    const labels = data.map(entry => entry.model);
                    const counts = data.map(entry => entry.total);
    
                    // Update chart
                    phishingByModelChart.data.labels = labels;
                    phishingByModelChart.data.datasets[0].data = counts;
                    phishingByModelChart.update();
                })
                .catch(error => {
                    console.error('Error fetching phishing email count by model:', error);
                });
        }
        const phishingByModelCtx = document.getElementById('phishingByModelChart').getContext('2d');
        const phishingByModelChart = new Chart(phishingByModelCtx, {
            type: 'doughnut',
            data: {
                labels: [], // To be updated dynamically from API
                datasets: [{
                    data: [], // To be updated dynamically from API
                    backgroundColor: [
                        'rgba(75, 192, 192, 0.2)',
                        'rgba(255, 206, 86, 0.2)',
                        'rgba(54, 162, 235, 0.2)',
                        'rgba(255, 99, 132, 0.2)',
                        'rgba(153, 102, 255, 0.2)'
                    ],
                    borderColor: [
                        'rgba(75, 192, 192, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 99, 132, 1)',
                        'rgba(153, 102, 255, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'right',
                        align: 'center',
                        labels: {
                            boxWidth: 20,
                            padding: 15
                        }
                    }
                }
            }
        });
    
        // Call fetchPhishingEmailByModel when page is loaded
        fetchPhishingEmailByModel();
    
        // Set up data refresh every 5 seconds
        setInterval(fetchPhishingEmailByModel, 5000);

        // Top Targeted Users (Horizontal Bar Chart)
        function fetchTopTargetedUsers() {
            fetch('http://127.0.0.1:5002/api/emails/top-users-with-phishing')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok ' + response.statusText);
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('API response:', data);
    
                    // Get data from API
                    const labels = data.map(entry => entry.toRecipientName);
                    const counts = data.map(entry => entry.total);
    
                    // Update chart
                    topTargetedUsersChart.data.labels = labels;
                    topTargetedUsersChart.data.datasets[0].data = counts;
                    topTargetedUsersChart.update();
                })
                .catch(error => {
                    console.error('Error fetching top targeted users:', error);
                });
        }
        const topTargetedUsersCtx = document.getElementById('topTargetedUsersChart').getContext('2d');
        const topTargetedUsersChart = new Chart(topTargetedUsersCtx, {
            type: 'bar',
            data: {
                labels: [], // To be updated dynamically from API
                datasets: [
                    {
                        data: [], // To be updated dynamically from API
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.2)',  // Color for User1
                            'rgba(54, 162, 235, 0.2)',  // Color for User2
                            'rgba(255, 206, 86, 0.2)',  // Color for User3
                            'rgba(75, 192, 192, 0.2)',  // Color for User4
                            'rgba(153, 102, 255, 0.2)'  // Color for User5
                        ],
                        borderColor: [
                            'rgba(255, 99, 132, 1)',  // Color for User1
                            'rgba(54, 162, 235, 1)',  // Color for User2
                            'rgba(255, 206, 86, 1)',  // Color for User3
                            'rgba(75, 192, 192, 1)',  // Color for User4
                            'rgba(153, 102, 255, 1)'  // Color for User5
                        ],
                        borderWidth: 1
                    }
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false, // Ensure the chart respects the container size
                plugins: {
                    legend: {
                        display: false // Hide legend
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true
                    },
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

    
        // Call fetchTopTargetedUsers when page is loaded
        fetchTopTargetedUsers();
    
        // Set up data refresh every 5 seconds
        //setInterval(fetchTopTargetedUsers, 5000);
    }
});
