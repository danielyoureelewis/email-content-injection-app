//this function handles newsletter signup - host header content injection
function handleSignUP(e) {
  console.log(e);
  showNotification('🔮 Your Fate is Sealed... Welcome to Tentacle & Throw! 🔮 The stars have shifted, the ancient ones have whispered, and your email has been claimed.')
  e.preventDefault()
  let options = {
    method: 'POST',
    headers: {}
  };
  let email = document.getElementById('signUpEmail').value;
  let username = sessionStorage.getItem('username');
  console.log(email)
  if (email.includes('@')) {
    fetch('/signup', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        // Your data to send
        email,
        username
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
        const alertContainer = document.getElementById('signup-alert-container');

        if (data.message && data.message.includes('Signup successful!')) {
          document.getElementById('signin-name').value = document.getElementById('signup-name').value;
          //put signin-name in session storage
          document.getElementById('signin-password').value = document.getElementById('signup-password').value;
          $('[href="#signin"]').tab('show');
        } else if (data.message.includes('already exists!')) {
          // Clear fields
          console.log('username already exists!');
          document.getElementById('signup-name').value = '';
          document.getElementById('signup-password').value = '';
          document.getElementById('signup-email').value = '';
          $('[href="#signup"]').tab('show');
          // Show Bootstrap alert
          // Inside your .then(data => { ... }) block
          const alertContainer = document.getElementById('signup-alert-container');
          alertContainer.innerHTML = `<div class="alert alert-danger alert-dismissible fade in" role="alert">
          <button type="button" class="close" data-dismiss="alert" aria-label="Close">&times;</button>
          <strong>Error:</strong> ${data.message} </div>`;
        } else {
          console.log('something went wrong!');
        }
      })
      .catch(error => {
        console.log('Error:', error);
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
  // get username from session storage
  let username = document.getElementById('signin-name').value
  let password = document.getElementById('signin-password').value


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
      if (data.message && data.message.includes('successful!')) {
        console.log("here");
        sessionStorage.setItem('username', username);
        $("#authinputs-1").hide();
        $("#mfa").show();
        //document.getElementById('mfa').hidden = false;
        //document.getElementById('authinputs-1').hidden = true;
      } else if (data.message && data.message.includes('Invalid')) {
        console.log("Error signing in:", data.message);
        const alertContainer = document.getElementById('signin-alert-container');
        alertContainer.innerHTML = `<div class="alert alert-danger alert-dismissible fade in" role="alert">
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">&times;</button>
        <strong>Error:</strong> ${data.message} </div>`;
      }

      // Handle the response data
    })
    .catch(error => {
      console.log('Error:', error);
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
      if (data.successful) {
        document.location = '/';
      } else {
        // Handle invalid MFA code
        console.log("Error signing in:", data);
        document.getElementById('mfa').hidden = false;
        document.getElementById('authinputs-1').hidden = true;
        showNotification(`❌ Invalid MFA code. Please try again.`);
      }
    })
    .catch(error => {
      // Handle errors
    });
}

function support_modal(e) {
  if (e) { e.preventDefault() } // Prevent the link from navigating
  console.log("Support clicked"); // Debugging to confirm function is firing
  $('#exampleModalCenter').modal('show'); // Show the modal manually
  console.log("Modal shown"); // Debugging to confirm modal is shown
}

// Handles support feedback submission
function support(e) {
  console.log(e);
  e.preventDefault();

  let body = document.getElementById('support-body').value;
  let email_addr = 'support@tentacleandthrow.local';
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

function addToCart(e, item) {
  console.log(e);
  e.preventDefault();
  console.log(item);
  showNotification(`🦑 The tendrils accept your offering.`);
  fetch('/cart/add', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      item,
    })
  })
    //.then(response => response.json())
    .then(data => {
      console.log(data);
      if (data.status === 401) {
        console.log("Error adding product to cart:", data.error);
        document.location = '/account';
        return;
      }
    }
    )
}

// Handles forgot password functionality
function handleForgotPassword(e) {
  e.preventDefault();

  let email = document.getElementById('forgot-password-email').value;
  console.log("User input for reset:", email);

  if (email.length > 0) {
    fetch('/forgot_password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email: email
      })
    })
      .then(response => response.json())
      .then(data => {
        console.log("Password reset process initiated:", data);
        if (data.success) {
          showNotification(`🔑 A password reset link has been sent to ${email}.`);
          //show login tab
          document.getElementById('forgot-password-email').value = '';
          document.getElementById('signin-name').value = email;
          document.getElementById('signin-password').value = '';
          $('[href="#signin"]').tab('show');
        } else {
          showNotification(`❌ Error: ${data.message}`);
        }
      })
      .catch(error => {
        console.error("Error initiating password reset:", error);
      });
  }
}

function showNotification(message) {
  const notification = document.getElementById('notification');
  const messageSpan = document.getElementById('notification-message');

  messageSpan.innerText = message;
  notification.classList.add('show');
  notification.style.display = 'block';

  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => {
      notification.style.display = 'none';
    }, 700); // match transition time
  }, 3000);
}

function deleteCartItem(productId, card) {
  showNotification(`☠️ A sacrifice has been undone.`);
  fetch('/cart/delete', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ product_id: productId })
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        card.remove();
        updateCartSummary(); // Update the summary after item removal
      } else {
        console.error("Failed to delete item:", data.message);
      }
    })
    .catch(err => console.error("Error deleting item:", err));
}

function updateCartQuantity(productId, action, card) {
  console.log(action);
  if (action === 'increase') {
    showNotification(`🦑 The tendrils accept your offering.`);
  }
  else if (action === 'decrease') {
    showNotification(`☠️ A sacrifice has been undone.`);
  }
  fetch('/update_cart', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      product_id: productId,
      action: action
    })
  })
    .then(response => response.json())
    .then(data => {
      card.querySelector('.quantity').textContent = data.new_quantity;
      updateCartSummary(); // Update the summary after quantity change
    })
    .catch(err => console.error('Update failed:', err));
}

// Handle checkout button click
function proceedToCheckout() {
  window.location.href = '/checkout'; // Redirect to checkout page
}

// Update the total price based on cart content
function updateCartSummary() {
  let subtotal = 0;
  document.querySelectorAll('.cart-card').forEach(card => {
    let price = parseFloat(card.querySelector('.price').textContent.replace('$', ''));
    let quantity = parseInt(card.querySelector('.quantity').textContent);
    subtotal += price * quantity;
  });
  document.getElementById('subtotal').textContent = `$${subtotal.toFixed(2)}`;
  let shipping = 5.00; // Default shipping cost
  let total = subtotal + shipping;
  document.getElementById('shipping').textContent = `$${shipping.toFixed(2)}`;
  document.getElementById('total').textContent = `$${total.toFixed(2)}`;
}

if (!localStorage.getItem("player_id")) {
  localStorage.setItem("player_id", crypto.randomUUID());
}

function submitSolution(uuid) {
  const player_id = sessionStorage.getItem("player_id");

  fetch(`/api/solve/${uuid}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_id: player_id })
  })
  .then(res => res.json())
  .then(data => {
      alert(data.message);
      loadChallenges();
  });
}
