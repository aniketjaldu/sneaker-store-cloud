import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { FaArrowLeft, FaBox, FaTruck, FaCheckCircle, FaClock, FaEye } from 'react-icons/fa';
import api from '../utils/api';

const OrderDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrderDetails();
  }, [id]);

  const fetchOrderDetails = async () => {
    try {
      const response = await api.get(`/orders/${id}`);
      setOrder(response.data);
    } catch (error) {
      console.error('Error fetching order details:', error);
      if (error.response?.status === 404) {
        navigate('/orders');
      }
    } finally {
      setLoading(false);
    }
  };

  const getOrderStatus = (status) => {
    const statusConfig = {
      'pending': { icon: FaClock, color: 'text-yellow-600', bgColor: 'bg-yellow-100', text: 'Pending' },
      'processing': { icon: FaBox, color: 'text-blue-600', bgColor: 'bg-blue-100', text: 'Processing' },
      'shipped': { icon: FaTruck, color: 'text-purple-600', bgColor: 'bg-purple-100', text: 'Shipped' },
      'delivered': { icon: FaCheckCircle, color: 'text-green-600', bgColor: 'bg-green-100', text: 'Delivered' },
      'cancelled': { icon: FaEye, color: 'text-red-600', bgColor: 'bg-red-100', text: 'Cancelled' }
    };

    const config = statusConfig[status] || statusConfig['pending'];
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${config.bgColor} ${config.color}`}>
        <Icon className="w-4 h-4 mr-2" />
        {config.text}
      </span>
    );
  };

  const calculateOrderTotal = (items) => {
    return Math.round(items.reduce((total, item) => {
      const itemTotal = item.item_total || (item.current_price || item.market_price || 0) * item.quantity;
      return total + itemTotal;
    }, 0) * 100) / 100;
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Order not found</h2>
        <Link to="/orders" className="text-primary-600 hover:text-primary-700">
          Back to orders
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link
            to="/orders"
            className="flex items-center space-x-2 text-primary-600 hover:text-primary-700"
          >
            <FaArrowLeft />
            <span>Back to Orders</span>
          </Link>
        </div>
      </div>

      {/* Order Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Order #{order.order_id}
            </h1>
            <p className="text-gray-600 mt-2">
              Placed on {new Date(order.order_date).toLocaleDateString()} at {new Date(order.order_date).toLocaleTimeString()}
            </p>
          </div>
          <div className="text-right">
            {getOrderStatus(order.order_status || 'pending')}
          </div>
        </div>

        {/* Order Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Order Information</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Order ID:</span>
                <span className="font-medium">#{order.order_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Order Date:</span>
                <span className="font-medium">{new Date(order.order_date).toLocaleDateString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Status:</span>
                <span className="font-medium capitalize">{order.order_status || 'pending'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Email:</span>
                <span className="font-medium">{order.email}</span>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Order Summary</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Items:</span>
                <span className="font-medium">{order.items?.length || 0}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Subtotal:</span>
                <span className="font-medium">${calculateOrderTotal(order.items || []).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Tax (8%):</span>
                <span className="font-medium">${(calculateOrderTotal(order.items || []) * 0.08).toFixed(2)}</span>
              </div>
              <div className="flex justify-between border-t pt-2">
                <span className="text-gray-900 font-semibold">Total:</span>
                <span className="text-gray-900 font-bold">${(calculateOrderTotal(order.items || []) * 1.08).toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Order Items */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Order Items</h2>
        </div>
        
        <div className="divide-y divide-gray-200">
          {order.items?.map((item, index) => (
            <div key={index} className="px-6 py-4">
              <div className="flex items-center space-x-4">
                {/* Product Image */}
                <div className="w-20 h-20 bg-gray-200 rounded-lg flex items-center justify-center">
                  <span className="text-gray-500 text-sm">
                    {item.product_name || 'Product'}
                  </span>
                </div>

                {/* Product Info */}
                <div className="flex-1">
                  <h3 className="text-lg font-medium text-gray-900">
                    {item.product_name}
                  </h3>
                  <p className="text-gray-600">
                    {item.brand_name} • Qty: {item.quantity}
                  </p>
                  {item.description && (
                    <p className="text-sm text-gray-500 mt-1">
                      {item.description}
                    </p>
                  )}
                </div>

                {/* Price */}
                <div className="text-right">
                  <p className="text-lg font-medium text-gray-900">
                    ${(item.item_total || (item.current_price || item.market_price || 0) * item.quantity).toFixed(2)}
                  </p>
                  <p className="text-sm text-gray-500">
                    ${(item.current_price || item.market_price).toFixed(2)} each
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Order Status Timeline */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Order Timeline</h3>
        <div className="space-y-4">
          <div className="flex items-center space-x-4">
            <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
              <FaCheckCircle className="w-4 h-4 text-white" />
            </div>
            <div>
              <p className="font-medium text-gray-900">Order Placed</p>
              <p className="text-sm text-gray-600">{new Date(order.order_date).toLocaleDateString()}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
              order.order_status === 'processing' || order.order_status === 'shipped' || order.order_status === 'delivered' 
                ? 'bg-blue-500' : 'bg-gray-300'
            }`}>
              <FaBox className={`w-4 h-4 ${order.order_status === 'processing' || order.order_status === 'shipped' || order.order_status === 'delivered' ? 'text-white' : 'text-gray-500'}`} />
            </div>
            <div>
              <p className="font-medium text-gray-900">Processing</p>
              <p className="text-sm text-gray-600">Preparing your order</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
              order.order_status === 'shipped' || order.order_status === 'delivered' 
                ? 'bg-purple-500' : 'bg-gray-300'
            }`}>
              <FaTruck className={`w-4 h-4 ${order.order_status === 'shipped' || order.order_status === 'delivered' ? 'text-white' : 'text-gray-500'}`} />
            </div>
            <div>
              <p className="font-medium text-gray-900">Shipped</p>
              <p className="text-sm text-gray-600">On its way to you</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
              order.order_status === 'delivered' 
                ? 'bg-green-500' : 'bg-gray-300'
            }`}>
              <FaCheckCircle className={`w-4 h-4 ${order.order_status === 'delivered' ? 'text-white' : 'text-gray-500'}`} />
            </div>
            <div>
              <p className="font-medium text-gray-900">Delivered</p>
              <p className="text-sm text-gray-600">Order completed</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrderDetail; 