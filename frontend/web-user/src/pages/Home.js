import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FaArrowRight, FaStar, FaShoppingCart } from 'react-icons/fa';
import axios from 'axios';

const Home = () => {
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFeaturedProducts = async () => {
      try {
        const response = await axios.get('/inventory', {
          params: {
            limit: 6,
            sort_by: 'discount',
            sort_order: 'desc'
          }
        });
        const data = response.data;
        if (Array.isArray(data)) {
          setFeaturedProducts(data);
        } else if (data && Array.isArray(data.products)) {
          setFeaturedProducts(data.products);
        } else {
          setFeaturedProducts([]);
        }
              } catch (error) {
          console.error('Error fetching featured products:', error);
          setFeaturedProducts([]);
        } finally {
          setLoading(false);
        }
    };

    fetchFeaturedProducts();
  }, []);

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-r from-primary-600 to-secondary-600 text-white py-20 rounded-2xl overflow-hidden">
        <div className="absolute inset-0 bg-black opacity-20"></div>
        <div className="relative z-10 text-center">
          <h1 className="text-5xl md:text-6xl font-bold mb-6">
            Step into Style
          </h1>
          <p className="text-xl md:text-2xl mb-8 max-w-2xl mx-auto">
            Discover the latest trends in footwear. From classic sneakers to premium boots, 
            we have everything you need to make a statement.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link 
              to="/products" 
              className="bg-white text-primary-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors flex items-center justify-center space-x-2"
            >
              <span>Shop Now</span>
              <FaArrowRight />
            </Link>
            <Link 
              to="/register" 
              className="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:text-primary-600 transition-colors"
            >
              Join Us
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="grid md:grid-cols-3 gap-8">
        <div className="text-center p-6 bg-white rounded-lg shadow-md">
          <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <FaShoppingCart className="text-primary-600 text-2xl" />
          </div>
          <h3 className="text-xl font-semibold mb-2">Free Shipping</h3>
          <p className="text-gray-600">Free shipping on all orders over $50</p>
        </div>
        
        <div className="text-center p-6 bg-white rounded-lg shadow-md">
          <div className="w-16 h-16 bg-secondary-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <FaStar className="text-secondary-600 text-2xl" />
          </div>
          <h3 className="text-xl font-semibold mb-2">Premium Quality</h3>
          <p className="text-gray-600">Authentic products from top brands</p>
        </div>
        
        <div className="text-center p-6 bg-white rounded-lg shadow-md">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold mb-2">Easy Returns</h3>
          <p className="text-gray-600">30-day return policy for your peace of mind</p>
        </div>
      </section>

      {/* Featured Products */}
      <section>
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-3xl font-bold text-gray-800">Featured Products</h2>
          <Link 
            to="/products" 
            className="text-primary-600 hover:text-primary-700 font-semibold flex items-center space-x-1"
          >
            <span>View All</span>
            <FaArrowRight />
          </Link>
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="loading-spinner"></div>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {featuredProducts.slice(0, 6).map((product) => (
              <div key={product.id} className="bg-white rounded-lg shadow-md overflow-hidden product-card">
                <div className="aspect-w-1 aspect-h-1 bg-gray-200">
                  <div className="w-full h-48 bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center">
                    <span className="text-gray-500 text-lg font-medium">
                      {product.product_name || 'Product Image'}
                    </span>
                  </div>
                </div>
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-2">
                    {product.product_name}
                  </h3>
                  <p className="text-gray-600 text-sm mb-3">
                    {product.brand_name}
                  </p>
                  <div className="flex justify-between items-center">
                    <div className="flex items-center space-x-2">
                      <span className="text-2xl font-bold text-primary-600">
                        ${product.current_price || product.market_price}
                      </span>
                      {product.discount_percent > 0 && (
                        <span className="text-sm text-red-600 font-medium">
                          -{product.discount_percent}%
                        </span>
                      )}
                    </div>
                    <Link 
                      to={`/products/${product.id}`}
                      className="bg-primary-500 text-white px-4 py-2 rounded-lg hover:bg-primary-600 transition-colors"
                    >
                      View Details
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* CTA Section */}
      <section className="bg-gradient-to-r from-gray-800 to-gray-900 text-white py-16 rounded-2xl text-center">
        <h2 className="text-3xl md:text-4xl font-bold mb-4">
          Ready to Find Your Perfect Fit?
        </h2>
        <p className="text-xl mb-8 max-w-2xl mx-auto">
          Join thousands of satisfied customers who trust us for their footwear needs.
        </p>
        <Link 
          to="/products" 
          className="bg-primary-500 text-white px-8 py-3 rounded-lg font-semibold hover:bg-primary-600 transition-colors inline-flex items-center space-x-2"
        >
          <span>Start Shopping</span>
          <FaArrowRight />
        </Link>
      </section>
    </div>
  );
};

export default Home; 