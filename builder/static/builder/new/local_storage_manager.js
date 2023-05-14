/* jshint esversion: 6 */

let LocalStorageManagerClass = class LocalStorageManager {

    static ONE_MINUTE = 1000 * 60;
    static ONE_HOUR = LocalStorageManager.ONE_MINUTE * 60;
    static ONE_DAY = LocalStorageManager.ONE_HOUR * 24;
    static ONE_WEEK = LocalStorageManager.ONE_DAY * 7;

    constructor() { }

    set(key, value, ttl=LocalStorageManager.ONE_DAY) {
        const now = new Date();
        const item = {
            value: value,
            expiry: now.getTime() + ttl,
        };
        localStorage.setItem(key, JSON.stringify(item));
    }

    get(key) {
        const itemStr = localStorage.getItem(key);
        if (!itemStr) {
            return null;
        }

        const item = JSON.parse(itemStr);
        const now = new Date();

        if (now.getTime() > item.expiry) {
            localStorage.removeItem(key);
            return null;
        }
        return item.value;
    }

};