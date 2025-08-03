import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { FaSearch, FaFilter, FaStar, FaShoppingCart } from 'react-icons/fa';
import api from '../utils/api';

const Products = () => {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    brand: '',
    min_price: '',
    max_price: '',
    discount_only: false,
    search: '',
    sort_by: 'name',
    sort_order: 'asc'
  });
  const [filterOptions, setFilterOptions] = useState({
    brands: [],
    price_range: {}
  });
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetchFilterOptions();
    fetchProducts();
  }, []);

  useEffect(() => {
    fetchProducts();
  }, [filters]);

  const fetchFilterOptions = async () => {
    try {
      const response = await api.get('/inventory/filters');
      setFilterOptions(response.data);
    } catch (error) {
      console.error('Error fetching filter options:', error);
    }
  };

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const params = { ...filters };
      // Remove empty values
      Object.keys(params).forEach(key => {
        if (params[key] === '' || params[key] === null) {
          delete params[key];
        }
      });
      
      const response = await api.get('/inventory', { params });
      const data = response.data;
      if (Array.isArray(data)) {
        setProducts(data);
      } else if (data && Array.isArray(data.products)) {
        setProducts(data.products);
      } else {
        setProducts([]);
      }
    } catch (error) {
      console.error('Error fetching products:', error);
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const clearFilters = () => {
    setFilters({
      brand: '',
      min_price: '',
      max_price: '',
      discount_only: false,
      search: '',
      sort_by: 'name',
      sort_order: 'asc'
    });
  };

  const addToCart = async (productId) => {
    try {
      await api.post('/cart/add', null, {
        params: { product_id: productId, quantity: 1 }
      });
      alert('Product added to cart successfully!');
    } catch (error) {
      console.error('Error adding to cart:', error);
      if (error.response?.status === 401) {
        const shouldLogin = window.confirm('You need to login to add items to cart. Would you like to login now?');
        if (shouldLogin) {
          navigate('/login');
        }
      } else {
        alert('Failed to add product to cart. Please try again.');
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Products</h1>
          <p className="text-gray-600">Discover our collection of premium footwear</p>
        </div>
        
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <FaFilter />
            <span>Filters</span>
          </button>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
              <div className="relative">
                <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  value={filters.search}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
                  placeholder="Search products..."
                  className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
            </div>

            {/* Brand Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Brand</label>
              <select
                value={filters.brand}
                onChange={(e) => handleFilterChange('brand', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">All Brands</option>
                {filterOptions.brands?.map((brand) => (
                  <option key={brand.brand_id || brand} value={brand.brand_name || brand}>
                    {brand.brand_name || brand}
                  </option>
                ))}
              </select>
            </div>

            {/* Price Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Price Range</label>
              <div className="flex space-x-2">
                <input
                  type="number"
                  placeholder="Min"
                  value={filters.min_price}
                  onChange={(e) => handleFilterChange('min_price', e.target.value)}
                  className="w-1/2 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
                <input
                  type="number"
                  placeholder="Max"
                  value={filters.max_price}
                  onChange={(e) => handleFilterChange('max_price', e.target.value)}
                  className="w-1/2 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
            </div>

            {/* Sort */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Sort By</label>
              <div className="flex space-x-2">
                <select
                  value={filters.sort_by}
                  onChange={(e) => handleFilterChange('sort_by', e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="name">Name</option>
                  <option value="price">Price</option>
                  <option value="brand">Brand</option>
                  <option value="discount">Discount</option>
                </select>
                <select
                  value={filters.sort_order}
                  onChange={(e) => handleFilterChange('sort_order', e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="asc">Asc</option>
                  <option value="desc">Desc</option>
                </select>
              </div>
            </div>
          </div>

          {/* Additional Filters */}
          <div className="mt-4 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={filters.discount_only}
                  onChange={(e) => handleFilterChange('discount_only', e.target.checked)}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">Discounted Only</span>
              </label>
            </div>
            
            <button
              onClick={clearFilters}
              className="text-sm text-gray-600 hover:text-gray-800"
            >
              Clear Filters
            </button>
          </div>
        </div>
      )}

      {/* Products Grid */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="loading-spinner"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {products.map((product) => (
            <div key={product.product_id} className="bg-white rounded-lg shadow-md overflow-hidden product-card">
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
                    to={`/products/${product.product_id}`}
                    className="flex-1 bg-primary-500 text-white px-4 py-2 rounded-lg hover:bg-primary-600 transition-colors text-center"
                  >
                    View Details
                  </Link>
                  <button
                    onClick={() => addToCart(product.product_id)}
                    className="bg-secondary-500 text-white px-4 py-2 rounded-lg hover:bg-secondary-600 transition-colors"
                  >
                    <FaShoppingCart />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* No Products */}
      {!loading && products.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 text-6xl mb-4">🔍</div>
          <h3 className="text-xl font-semibold text-gray-600 mb-2">No products found</h3>
          <p className="text-gray-500">Try adjusting your filters or search terms</p>
        </div>
      )}
    </div>
  );
};

export default Products; 