import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { FaTrash, FaArrowLeft, FaShoppingBag, FaCreditCard } from 'react-icons/fa';
import api from '../utils/api';

const Cart = () => {
  const [cartItems, setCartItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchCart();
  }, []);

  const fetchCart = async () => {
    try {
      const response = await api.get('/cart');
      setCartItems(Array.isArray(response.data) ? response.data : [response.data]);
    } catch (error) {
      console.error('Error fetching cart:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateQuantity = async (productId, newQuantity) => {
    if (newQuantity < 1) return;
    
    setUpdating(true);
    try {
      // Remove current item and add with new quantity
      await api.delete(`/cart/remove?product_id=${productId}`);
      if (newQuantity > 0) {
        await api.post('/cart/add', null, {
          params: { product_id: productId, quantity: newQuantity }
        });
      }
      await fetchCart();
    } catch (error) {
      console.error('Error updating quantity:', error);
    } finally {
      setUpdating(false);
    }
  };

  const removeItem = async (productId) => {
    try {
      await api.delete(`/cart/remove?product_id=${productId}`);
      await fetchCart();
    } catch (error) {
      console.error('Error removing item:', error);
    }
  };

  const calculateSubtotal = () => {
    return cartItems.reduce((total, item) => {
      const price = item.current_price || item.market_price || 0;
      return total + (price * item.quantity);
    }, 0);
  };

  const calculateTax = () => {
    return calculateSubtotal() * 0.08; // 8% tax
  };

  const calculateTotal = () => {
    return calculateSubtotal() + calculateTax();
  };

  const handleCheckout = async () => {
    if (cartItems.length === 0) return;
    
    setCheckoutLoading(true);
    try {
      const response = await api.post('/orders', {});
      if (response.data.order_id) {
        // Redirect to orders page with success message
        navigate('/orders', { 
          state: { 
            message: `Order #${response.data.order_id} placed successfully! Check your email for confirmation.` 
          } 
        });
      }
    } catch (error) {
      console.error('Error creating order:', error);
      alert('Failed to create order. Please try again.');
    } finally {
      setCheckoutLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Shopping Cart</h1>
          <p className="text-gray-600">
            {cartItems.length} {cartItems.length === 1 ? 'item' : 'items'} in your cart
          </p>
        </div>
        <Link
          to="/products"
          className="flex items-center space-x-2 text-primary-600 hover:text-primary-700"
        >
          <FaArrowLeft />
          <span>Continue Shopping</span>
        </Link>
      </div>

      {cartItems.length === 0 ? (
        /* Empty Cart */
        <div className="text-center py-12">
          <div className="text-gray-400 text-6xl mb-4">🛒</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Your cart is empty</h2>
          <p className="text-gray-600 mb-8">Looks like you haven't added any items to your cart yet.</p>
          <Link
            to="/products"
            className="bg-primary-500 text-white px-6 py-3 rounded-lg hover:bg-primary-600 transition-colors inline-flex items-center space-x-2"
          >
            <FaShoppingBag />
            <span>Start Shopping</span>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Cart Items */}
          <div className="lg:col-span-2 space-y-4">
            {cartItems.map((item) => (
              <div key={item.product_id} className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center space-x-4">
                  {/* Product Image */}
                  <div className="w-24 h-24 bg-gray-200 rounded-lg flex items-center justify-center">
                    <span className="text-gray-500 text-sm">
                      {item.product_name || 'Product'}
                    </span>
                  </div>

                  {/* Product Info */}
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-1">
                      {item.product_name}
                    </h3>
                    <p className="text-gray-600 text-sm mb-2">
                      {item.brand_name}
                    </p>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        {/* Quantity Controls */}
                        <div className="flex items-center border border-gray-300 rounded-lg">
                          <button
                            onClick={() => updateQuantity(item.product_id, item.quantity - 1)}
                            disabled={updating}
                            className="px-3 py-1 text-gray-600 hover:text-gray-800 disabled:opacity-50"
                          >
                            -
                          </button>
                          <span className="px-4 py-1 border-x border-gray-300">
                            {item.quantity}
                          </span>
                          <button
                            onClick={() => updateQuantity(item.product_id, item.quantity + 1)}
                            disabled={updating}
                            className="px-3 py-1 text-gray-600 hover:text-gray-800 disabled:opacity-50"
                          >
                            +
                          </button>
                        </div>

                        {/* Price */}
                        <div className="text-right">
                          <div className="flex items-center space-x-2">
                            <span className="text-lg font-bold text-primary-600">
                              ${(item.current_price || item.market_price || 0) * item.quantity}
                            </span>
                            {item.discount_percent > 0 && (
                              <span className="text-sm text-red-600">
                                -{item.discount_percent}%
                              </span>
                            )}
                          </div>
                          <p className="text-sm text-gray-500">
                            ${item.current_price || item.market_price} each
                          </p>
                        </div>
                      </div>

                      {/* Remove Button */}
                      <button
                        onClick={() => removeItem(item.product_id)}
                        className="text-red-500 hover:text-red-700 p-2"
                      >
                        <FaTrash />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Order Summary */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-md p-6 sticky top-4">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Order Summary</h2>
              
              <div className="space-y-3 mb-6">
                <div className="flex justify-between">
                  <span className="text-gray-600">Subtotal</span>
                  <span className="font-medium">${calculateSubtotal().toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Tax (8%)</span>
                  <span className="font-medium">${calculateTax().toFixed(2)}</span>
                </div>
                <div className="border-t pt-3">
                  <div className="flex justify-between">
                    <span className="text-lg font-bold text-gray-900">Total</span>
                    <span className="text-lg font-bold text-primary-600">
                      ${calculateTotal().toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Shipping Info */}
              <div className="border-t pt-4 mb-6">
                <h3 className="font-semibold text-gray-900 mb-2">Shipping</h3>
                <p className="text-sm text-gray-600">
                  Free shipping on orders over $50
                </p>
                {calculateSubtotal() >= 50 ? (
                  <p className="text-green-600 text-sm font-medium">✓ Free shipping applied</p>
                ) : (
                  <p className="text-gray-600 text-sm">
                    Add ${(50 - calculateSubtotal()).toFixed(2)} more for free shipping
                  </p>
                )}
              </div>

              {/* Checkout Button */}
              <button 
                onClick={handleCheckout}
                disabled={checkoutLoading || cartItems.length === 0}
                className="w-full bg-primary-500 text-white py-3 px-6 rounded-lg hover:bg-primary-600 transition-colors flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {checkoutLoading ? (
                  <div className="loading-spinner w-5 h-5"></div>
                ) : (
                  <>
                    <FaCreditCard />
                    <span>Proceed to Checkout</span>
                  </>
                )}
              </button>

              {/* Additional Info */}
              <div className="mt-4 text-xs text-gray-500 space-y-1">
                <p>• Secure checkout with SSL encryption</p>
                <p>• 30-day return policy</p>
                <p>• Free shipping on orders over $50</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Cart; 