package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"github.com/hashicorp/terraform-plugin-sdk/v2/helper/schema"
)

type TransactionResponse struct {
	TransactionPollingURL string `json:"transactionPollingUrl"`
	CDOTransactionStatus  string `json:"cdoTransactionStatus"`
	EntityUid             string `json:"entityUid"`
}

func resourceFTDDevice() *schema.Resource {
	return &schema.Resource{
		Create: resourceFTDDeviceCreate,
		Read:   resourceFTDDeviceRead,
		Delete: resourceFTDDeviceDelete,

		Schema: map[string]*schema.Schema{
			"name": {
				Type:     schema.TypeString,
				Required: true,
				ForceNew: true,
			},
			"serial_number": {
				Type:     schema.TypeString,
				Required: true,
				ForceNew: true,
			},
			"access_policy_uuid": {
				Type:     schema.TypeString,
				Required: true,
				ForceNew: true,
			},
			"admin_password": {
				Type: 	schema.TypeString,
				Optional: true,
				ForceNew: true,
			},
		},

		Timeouts: &schema.ResourceTimeout{
			Create: schema.DefaultTimeout(30 * time.Minute),
			Delete: schema.DefaultTimeout(30 * time.Minute),
		},
	}
}

func resourceFTDDeviceCreate(d *schema.ResourceData, m interface{}) error {
	config := m.(*ProviderConfig)

	payload := map[string]interface{}{
		"name":              d.Get("name").(string),
		"serialNumber":      d.Get("serial_number").(string),
		"fmcAccessPolicyUid": d.Get("access_policy_uuid").(string),
		"licenses":          []string{"BASE"},
		"adminPassword":     d.Get("admin_password").(string),
	}

	resp, err := makeRequest(
		"POST",
		fmt.Sprintf("%s/api/rest/v1/inventory/devices/ftds/ztp", config.BaseURL),
		config.Token,
		payload,
	)
	if err != nil {
		return fmt.Errorf("Error creating FTD device: %s", err)
	}

	var transaction TransactionResponse
	if err := json.Unmarshal(resp, &transaction); err != nil {
		return fmt.Errorf("Error parsing response: %s", err)
	}

	if err := pollTransaction(config.Token, transaction.TransactionPollingURL); err != nil {
		d.SetId(transaction.EntityUid)
		return err
	}

	d.SetId(transaction.EntityUid)
	return nil
}

func resourceFTDDeviceRead(d *schema.ResourceData, m interface{}) error {
	// In this implementation, we'll assume the device exists if we successfully created it
	// A more complete implementation would verify the device's existence via API
	return nil
}

func resourceFTDDeviceDelete(d *schema.ResourceData, m interface{}) error {
	config := m.(*ProviderConfig)

	resp, err := makeRequest(
		"POST",
		fmt.Sprintf("%s/api/rest/v1/inventory/devices/ftds/cdfmcManaged/%s/delete", config.BaseURL, d.Id()),
		config.Token,
		nil,
	)
	if err != nil {
		return fmt.Errorf("Error deleting FTD device: %s", err)
	}

	if bytes.Equal(resp, []byte("success")) {
		d.SetId("")
		return nil

	}

	var transaction TransactionResponse
	if err := json.Unmarshal(resp, &transaction); err != nil {
		return fmt.Errorf("Error parsing response: %s", err)
	}

	if err := pollTransaction(config.Token, transaction.TransactionPollingURL); err != nil {
		return err
	}

	d.SetId("")
	return nil
}

func makeRequest(method, url, token string, payload interface{}) ([]byte, error) {
	var body io.Reader
	if payload != nil {
		payloadBytes, err := json.Marshal(payload)
		if err != nil {
			return nil, err
		}
		body = strings.NewReader(string(payloadBytes))
	}

	req, err := http.NewRequest(method, url, body)
	if err != nil {
		return nil, err
	}

	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", token))
	if payload != nil {
		req.Header.Set("Content-Type", "application/json")
	}

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	acceptableResponseCodes := map[int]struct{}{
		http.StatusOK:                  {},
		http.StatusCreated:             {},
		http.StatusAccepted:            {},
		http.StatusNonAuthoritativeInfo: {},
		http.StatusNoContent:           {},
		http.StatusResetContent:        {},
		http.StatusPartialContent:      {},
	}
	if _, ok := acceptableResponseCodes[resp.StatusCode]; !ok {
		return nil, fmt.Errorf("API request failed with status %d", resp.StatusCode)
	}

	if resp.Body == nil {
		return []byte("success"), nil
	}

	return io.ReadAll(resp.Body)
}

func pollTransaction(token, pollingURL string) error {
	maxAttempts := 30
	delaySeconds := 10

	for attempt := 0; attempt < maxAttempts; attempt++ {
		resp, err := makeRequest("GET", pollingURL, token, nil)
		if err != nil {
			return err
		}

		var transaction TransactionResponse
		if err := json.Unmarshal(resp, &transaction); err != nil {
			return fmt.Errorf("Error parsing polling response: %s", err)
		}

		if transaction.CDOTransactionStatus == "DONE" {
			return nil
		}
		if transaction.CDOTransactionStatus == "ERROR" {
			return fmt.Errorf("Transaction failed with status ERROR")
		}

		time.Sleep(time.Duration(delaySeconds) * time.Second)
	}

	return fmt.Errorf("Transaction polling timed out after %d attempts", maxAttempts)
}
