import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FaBox, FaTruck, FaCheckCircle, FaClock, FaEye } from 'react-icons/fa';
import axios from 'axios';

const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await axios.get('/orders');
      setOrders(Array.isArray(response.data) ? response.data : [response.data]);
    } catch (error) {
      console.error('Error fetching orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const getOrderStatus = (status) => {
    const statusConfig = {
      'pending': { color: 'text-yellow-600', bg: 'bg-yellow-100', icon: FaClock },
      'processing': { color: 'text-blue-600', bg: 'bg-blue-100', icon: FaBox },
      'shipped': { color: 'text-purple-600', bg: 'bg-purple-100', icon: FaTruck },
      'delivered': { color: 'text-green-600', bg: 'bg-green-100', icon: FaCheckCircle },
      'cancelled': { color: 'text-red-600', bg: 'bg-red-100', icon: FaBox }
    };

    const config = statusConfig[status] || statusConfig['pending'];
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.color}`}>
        <Icon className="w-3 h-3 mr-1" />
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const calculateOrderTotal = (items) => {
    return items.reduce((total, item) => {
      const price = item.current_price || item.market_price || 0;
      return total + (price * item.quantity);
    }, 0);
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
      <div>
        <h1 className="text-3xl font-bold text-gray-900">My Orders</h1>
        <p className="text-gray-600">Track your order history and current shipments</p>
      </div>

      {orders.length === 0 ? (
        /* Empty Orders */
        <div className="text-center py-12">
          <div className="text-gray-400 text-6xl mb-4">📦</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">No orders yet</h2>
          <p className="text-gray-600 mb-8">Start shopping to see your orders here.</p>
          <Link
            to="/products"
            className="bg-primary-500 text-white px-6 py-3 rounded-lg hover:bg-primary-600 transition-colors inline-flex items-center space-x-2"
          >
            <FaBox />
            <span>Start Shopping</span>
          </Link>
        </div>
      ) : (
        /* Orders List */
        <div className="space-y-6">
          {orders.map((order) => (
            <div key={order.id} className="bg-white rounded-lg shadow-md overflow-hidden">
              {/* Order Header */}
              <div className="px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      Order #{order.id}
                    </h3>
                    <p className="text-sm text-gray-600">
                      Placed on {new Date(order.created_at || Date.now()).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center space-x-4">
                    {getOrderStatus(order.status || 'pending')}
                    <Link
                      to={`/orders/${order.id}`}
                      className="text-primary-600 hover:text-primary-700 flex items-center space-x-1"
                    >
                      <FaEye />
                      <span>View Details</span>
                    </Link>
                  </div>
                </div>
              </div>

              {/* Order Items */}
              <div className="px-6 py-4">
                <div className="space-y-3">
                  {order.items?.map((item, index) => (
                    <div key={index} className="flex items-center space-x-4">
                      {/* Product Image */}
                      <div className="w-16 h-16 bg-gray-200 rounded-lg flex items-center justify-center">
                        <span className="text-gray-500 text-xs">
                          {item.product_name || 'Product'}
                        </span>
                      </div>

                      {/* Product Info */}
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">
                          {item.product_name}
                        </h4>
                        <p className="text-sm text-gray-600">
                          {item.brand_name} • Qty: {item.quantity}
                        </p>
                      </div>

                      {/* Price */}
                      <div className="text-right">
                        <p className="font-medium text-gray-900">
                          ${(item.current_price || item.market_price || 0) * item.quantity}
                        </p>
                        <p className="text-sm text-gray-500">
                          ${item.current_price || item.market_price} each
                        </p>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Order Summary */}
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-sm text-gray-600">
                        {order.items?.length || 0} {order.items?.length === 1 ? 'item' : 'items'}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-gray-900">
                        Total: ${calculateOrderTotal(order.items || []).toFixed(2)}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Order Status Legend */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Order Status Guide</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="flex items-center space-x-2">
            <FaClock className="text-yellow-600" />
            <span className="text-sm text-gray-700">Pending - Order received</span>
          </div>
          <div className="flex items-center space-x-2">
            <FaBox className="text-blue-600" />
            <span className="text-sm text-gray-700">Processing - Preparing shipment</span>
          </div>
          <div className="flex items-center space-x-2">
            <FaTruck className="text-purple-600" />
            <span className="text-sm text-gray-700">Shipped - On the way</span>
          </div>
          <div className="flex items-center space-x-2">
            <FaCheckCircle className="text-green-600" />
            <span className="text-sm text-gray-700">Delivered - Order completed</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Orders; 