/*
 * Copyright (C) 2013 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package edu.umich.eecs.lab11.whereabouts;

import android.app.ListFragment;
import android.bluetooth.BluetoothDevice;
import android.content.Intent;
import android.graphics.drawable.Drawable;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.ImageView;
import android.widget.ListView;
import android.widget.TextView;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

/**
 * Activity for scanning and displaying available Bluetooth LE devices.
 */
public class NearYouFragment extends ListFragment {
    public LeDeviceListAdapter mLeDeviceListAdapter;
    private FragmentActivity fa;

    static NearYouFragment newInstance(int num) {
        NearYouFragment f = new NearYouFragment();

        // Supply num input as an argument.
        Bundle args = new Bundle();
        args.putInt("num", num);
        f.setArguments(args);

        return f;
    }

    @Override
    public View onCreateView(LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState) {
        fa = (FragmentActivity)super.getActivity();
        View v = inflater.inflate(R.layout.fragment_scan, container, false);
        ListView lv = (ListView)v.findViewById(android.R.id.list);
        lv.setEmptyView(v.findViewById(android.R.id.empty));
        return v;
    }

    @Override
    public void onResume() {
        mLeDeviceListAdapter = new LeDeviceListAdapter();
        setListAdapter(mLeDeviceListAdapter);
        fa.getJSON();
        super.onResume();
    }

    public class BTDevice {
        public BluetoothDevice device;
        public Integer rssi;
        public boolean keep;
        @Override
        public boolean equals(Object obj) {
            return ((obj instanceof BluetoothDevice) && obj.equals(this.device)) || ((obj instanceof BTDevice) && ((BTDevice)obj).device.equals(this.device));
        }
    }

    // Adapter for holding devices found through scanning.
    public class LeDeviceListAdapter extends BaseAdapter {
        private ArrayList<BTDevice> mLeDevices;
        private LayoutInflater mInflator;

        public LeDeviceListAdapter() {
            super();
            mLeDevices = new ArrayList<BTDevice>();
            mInflator = fa.getLayoutInflater();
        }

        public void addDevice(BluetoothDevice device, final int rssi) {
            BTDevice dev = new BTDevice();
            dev.device = device;
            dev.rssi = rssi;
            dev.keep = true;
            if(!mLeDevices.contains(dev)) {
                mLeDevices.add(dev);
            } else {
                mLeDevices.set(mLeDevices.indexOf(dev),dev);
            }
//            System.out.println(device.getAddress() + "," + );
            Collections.sort(mLeDevices, new Comparator<BTDevice>() {
                @Override
                public int compare(BTDevice bd1, BTDevice bd2)
                {
                    return (bd2.rssi-bd1.rssi);
                }
            });
        }

        public BTDevice getDevice(int position) {
            return mLeDevices.get(position);
        }

        public void clear() {
            for (Iterator<BTDevice> iterator = mLeDevices.iterator(); iterator.hasNext();) {
                BTDevice device = iterator.next();
                if (!device.keep) {
                    iterator.remove();
                } else {
                    device.keep=false;
                }
            }
        }

        @Override
        public int getCount() {
            return mLeDevices.size();
        }

        @Override
        public Object getItem(int i) {
            return mLeDevices.get(i);
        }

        @Override
        public long getItemId(int i) {
            return i;
        }

        @Override
        public View getView(int i, View view, ViewGroup viewGroup) {
            ViewHolder viewHolder;
            // General ListView optimization code.
            if (view == null) {
                view = mInflator.inflate(R.layout.listitem_device, null);
                viewHolder = new ViewHolder();
                viewHolder.deviceAddress = (TextView) view.findViewById(R.id.device_address);
                viewHolder.deviceName = (TextView) view.findViewById(R.id.device_name);
                viewHolder.image = (ImageView) view.findViewById(R.id.image);
                view.setTag(viewHolder);
            } else {
                viewHolder = (ViewHolder) view.getTag();
            }

            BTDevice dev = mLeDevices.get(i);
            BluetoothDevice device = dev.device;
            String[] addr = device.getAddress().split(":");
            String builder = "";
            for(int s=addr.length-1; s>=0; s--) builder+=addr[s];
            builder = device.getAddress().toLowerCase();
            String a = fa.profiles.getAsJsonObject(builder).get("full_name").toString();
            String[] b = a.split("\"");
            String deviceName = b[1];
            int resID = getResources().getIdentifier(String.valueOf(R.drawable.ic_launcher),"drawable",fa.getPackageName());
            viewHolder.image.setImageResource(resID);
            if (deviceName != null && deviceName.length() > 0)
                viewHolder.deviceName.setText(deviceName);
            else
                viewHolder.deviceName.setText(R.string.unknown_device);
            viewHolder.deviceAddress.setText(device.getAddress() + " | " + dev.rssi);
            try { viewHolder.image.setImageDrawable(Drawable.createFromStream(fa.getAssets().open("super/"+deviceName.replace(" ","-")+".jpg"),null)); } catch(Exception e) {}
            return view;
        }
    }

    static class ViewHolder {
        TextView deviceName;
        TextView deviceAddress;
        ImageView image;
    }

}