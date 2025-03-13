//this function handles newsletter signup - host header content injection
function handleSignUP(e) {
  console.log(e);
  e.preventDefault()
  let options = {
    method: 'POST',
    headers: {}
  };
  let email = document.getElementById('signUpEmail').value
  console.log(email)
  if (email.includes('@')) {
    fetch('/signup', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        // Your data to send
        email
      })
    })
      .then(response => response.json())
      .then(data => {
        // Handle the response data
      })
      .catch(error => {
        // Handle errors
      });
  }
}

//handles user registration - name content injection
function handleRegistration(e) {
  console.log(e);
  e.preventDefault()
  let options = {
    method: 'POST',
    headers: {}
  };
  let email = document.getElementById('signup-email').value
  let username = document.getElementById('signup-name').value
  let password = document.getElementById('signup-password').value
  console.log(email)
  if (email.includes('@')) {
    fetch('/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        // Your data to send
        username,
        password,
        email
      })
    })
      .then(response => response.json())
      .then(data => {
        // Check if the response contains the success message
        if (data.message && data.message.includes('Signup successful!')) {
          console.log('here')
          document.getElementById('signin-name').value = document.getElementById('signup-name').value;
          document.getElementById('signin-password').value = document.getElementById('signup-password').value;
          $('[href="#signin"]').tab('show');
        }
      })
      .catch(error => {
        // Handle errors
      });
  }

}

//this function handles newsletter signup - host header content injection
function handleSignIn(e) {
  console.log(e);
  e.preventDefault()
  let options = {
    method: 'POST',
    headers: {}
  };
  let username = document.getElementById('signin-name').value
  let password = document.getElementById('signin-password').value
  console.log('here')

  fetch('/signin', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      // Your data to send
      username,
      password
    })
  })
    .then(response => response.json())
    .then(data => {
      document.getElementById('mfa').hidden = false;
      document.getElementById('authinputs-1').hidden = true;
      // Handle the response data
    })
    .catch(error => {
      // Handle errors
    });
}


//this function handles newsletter signup - host header content injection
function handleMFA(e) {
  console.log(e);
  e.preventDefault()
  let options = {
    method: 'POST',
    headers: {}
  };
  let mfa = document.getElementById('signin-MFA').value
  console.log(mfa)
  fetch('/mfa', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      // Your data to send
      mfa
    })
  })
    .then(response => response.json())
    .then(data => {
      document.getElementById('mfa').hidden = true;
      document.getElementById('authinputs-1').hidden = false;
      // Handle the response data
    })
    .catch(error => {
      // Handle errors
    });
}

// Handles support feedback submission
function support(e) {
  console.log(e);
  e.preventDefault();

  let body = document.getElementById('support-body').value;
  let email_addr = 'support@online.store';
  let subject = 'Feedback';

  // Get the selected feedback option
  let selectedFeedback = document.querySelector('.feedback-btn.active');
  let feedback = selectedFeedback ? selectedFeedback.innerText : "No feedback selected";
  variables = { body, feedback, email_addr, subject };
  if (email_addr.includes('@')) {
    fetch('/support', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        variables
      })
    })
      .then(response => response.json())
      .then(data => {
        console.log("Feedback sent successfully:", data);
        $('#exampleModalCenter').modal('hide');
      })
      .catch(error => {
        console.error("Error sending feedback:", error);
      });
  }
}

// Handles forgot password functionality
function handleForgotPassword(e) {
  console.log(e);
  e.preventDefault();

  let email = document.getElementById('forgot-password-email').value;
  console.log(email);

  if (email.includes('@')) {
    fetch('/forgot-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email
      })
    })
      .then(response => response.json())
      .then(data => {
        // Handle the response data
        console.log("Password reset email sent successfully:", data);
      })
      .catch(error => {
        // Handle errors
        console.error("Error sending password reset email:", error);
      });
  }
}