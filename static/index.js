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
        const alertContainer = document.getElementById('signup-alert-container');

        if (data.message && data.message.includes('Signup successful!')) {
          document.getElementById('signin-name').value = document.getElementById('signup-name').value;
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
      console.log(data);      
      if (data.message && data.message.includes('successful!')) {
        document.getElementById('mfa').hidden = false;
        document.getElementById('authinputs-1').hidden = true;
      } else if (data.message && data.message.includes('Invalid username or password.')) {
        console.log("Error signing in:", data.message);
        const alertContainer = document.getElementById('signin-alert-container');
        alertContainer.innerHTML = `<div class="alert alert-danger alert-dismissible fade in" role="alert">
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">&times;</button>
        <strong>Error:</strong> ${data.message} </div>`;
      }
      
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

function support_modal(e) {
  if (e){e.preventDefault()} // Prevent the link from navigating
  console.log("Support clicked"); // Debugging to confirm function is firing
  $('#exampleModalCenter').modal('show'); // Show the modal manually
  console.log("Modal shown"); // Debugging to confirm modal is shown
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

function addToCart(e, item) {
  console.log(e);
  e.preventDefault();
  console.log(item);
  showCartNotification(`🦑 The tendrils accept your offering.`);
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
      })
      .catch(error => {
        console.error("Error initiating password reset:", error);
      });
  }
}

function showCartNotification(message) {
  const notification = document.getElementById('cart-notification');
  notification.innerText = message;
  notification.style.display = 'block';

  setTimeout(() => {
      notification.style.display = 'none';
  }, 2500);
}

function deleteCartItem(productId, card) {
  showCartNotification(`☠️ A sacrifice has been undone.`);
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
      showCartNotification(`🦑 The tendrils accept your offering.`);
  }
  else if (action === 'decrease') {
      showCartNotification(`☠️ A sacrifice has been undone.`);
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