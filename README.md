<h1>StockBrokerageSystem</h1>

<p><strong>StockBrokerageSystem</strong> is a microservices-based project designed for seamless order management in a stock trading environment. Users can place, modify, and cancel orders, which are recorded in an orderbook. Orders are executed once the best bid price exceeds the best ask price. The system is built with MongoDB and Redis to ensure data persistence and reliability during system failures, and it is deployed on Vercel.</p>

<h2>Key Features:</h2>

<h3>1. Order Management API</h3>
<p>Provides a CRUD interface for placing, modifying, canceling, and fetching orders.</p>
<ul>
  <li><strong>Place Order</strong> (POST): Allows users to submit a buy or sell order with a specified quantity and price, returning an <code>order_id</code>.</li>
  <li><strong>Modify Order</strong> (PUT): Updates an existing order’s price, ensuring efficient order book management.</li>
  <li><strong>Cancel Order</strong> (DELETE): Cancels an order if it has not been fully traded, or cancels the remaining quantity of a partially traded order.</li>
  <li><strong>Fetch Order</strong> (GET): Retrieves detailed order information, including the price, quantity, and average traded price.</li>
  <li><strong>Fetch All Orders</strong> (GET): Lists all orders placed, along with their detailed status.</li>
  <li><strong>Fetch All Trades</strong> (GET): Returns a comprehensive list of all executed trades, including unique trade identifiers, price, and timestamps.</li>
</ul>

<h3>2. WebSocket Integration</h3>
<p>The system leverages WebSocket to keep users updated with real-time trade and order book data:</p>
<ul>
  <li><strong>Trade Updates:</strong> Whenever a trade is executed, the system emits a notification via WebSocket, including trade details such as the execution timestamp, quantity, price, and the associated order IDs.</li>
  <li><strong>Order Book Snapshots:</strong> The top 5 levels of the order book for both bid and ask sides are broadcasted every second, providing real-time insight into market depth. Each depth level includes the price and quantity.</li>
</ul>

<h3>3. Resilient Architecture</h3>
<p>By utilizing MongoDB and Redis, <strong>StockBrokerageSystem</strong> maintains a robust infrastructure that recovers the system state after failures or restarts. Redis is employed for caching to ensure fast operations, while MongoDB acts as the primary datastore, ensuring long-term data persistence.</p>

<h2>Deployment</h2>
<p>The entire system is deployed on <strong>Vercel</strong>, offering a scalable and globally accessible platform for reliable performance.</p>
