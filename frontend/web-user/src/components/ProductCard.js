import React from 'react';
import { Link } from 'react-router-dom';
import { FaStar, FaShoppingCart } from 'react-icons/fa';

const ProductCard = ({ product, onAddToCart }) => {
  const handleAddToCart = (e) => {
    e.preventDefault();
    if (onAddToCart) {
      onAddToCart(product.id);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden product-card">
      <div className="aspect-w-1 aspect-h-1 bg-gray-200">
        <div className="w-full h-48 bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center">
          <span className="text-gray-500 text-lg font-medium">
            {product.product_name || 'Product Image'}
          </span>
        </div>
      </div>
      
      <div className="p-4">
        <h3 className="text-lg font-semibold text-gray-800 mb-2 line-clamp-2">
          {product.product_name}
        </h3>
        <p className="text-gray-600 text-sm mb-2">
          {product.brand_name}
        </p>
        
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <span className="text-xl font-bold text-primary-600">
              ${product.current_price || product.market_price}
            </span>
            {product.discount_percent > 0 && (
              <span className="text-sm text-red-600 font-medium">
                -{product.discount_percent}%
              </span>
            )}
          </div>
          <div className="flex items-center space-x-1">
            <FaStar className="text-yellow-400" />
            <span className="text-sm text-gray-600">4.5</span>
          </div>
        </div>
        
        <div className="flex space-x-2">
          <Link
            to={`/products/${product.id}`}
            className="flex-1 bg-primary-500 text-white px-4 py-2 rounded-lg hover:bg-primary-600 transition-colors text-center"
          >
            View Details
          </Link>
          <button
            onClick={handleAddToCart}
            className="bg-secondary-500 text-white px-4 py-2 rounded-lg hover:bg-secondary-600 transition-colors"
          >
            <FaShoppingCart />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProductCard; 