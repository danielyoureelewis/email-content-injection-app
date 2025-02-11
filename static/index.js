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
  let name = document.getElementById('signup-name').value
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
            name,
            password,
            email
          })
        })
        .then(response => response.json())
        .then(data => {
          // Check if the response contains the success message
          if (data.message && data.message.includes('Signup successful!')) {
            console.log('here')
            document.getElementById('signin-email').value = document.getElementById('signup-email').value;
            document.getElementById('signin-password').value = document.getElementById('signup-password').value;
            $('[href="#signin"]').tab('show');
          }
        })
        .catch(error => {
          // Handle errors
        });
  }
    
}